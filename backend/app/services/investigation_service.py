import logging

from app.agent.execution_manager_provider import (
    get_execution_manager,
)
from app.agent.langgraph_runtime import (
    LangGraphInvestigationOutcome,
    run_langgraph_investigation,
)
from app.exceptions.ai_exceptions import AIError
from app.models.investigation import Investigation, InvestigationStatus
from app.models.investigation_history import (
    InvestigationAction,
)
from app.models.parsed_log import ParsedLog
from app.repositories.investigation_repository import (
    InvestigationRepository,
)
from app.repositories.log_file_repository import (
    LogFileRepository,
)
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
)
from app.schemas.investigation_history import (
    InvestigationHistoryCreate,
)
from app.services.investigation_history_service import (
    InvestigationHistoryService,
)
from app.services.llm.ai_service import AIService
from app.services.llm.log_formatter import LogFormatter
from app.services.llm.schemas import AIInvestigationResponse
from app.services.parsed_log_service import ParsedLogService
from fastapi import HTTPException, status
from sqlmodel import Session

logger = logging.getLogger(__name__)
class InvestigationService:
    def __init__(
        self,
        repository: InvestigationRepository,
        history_service: InvestigationHistoryService,
        db: Session
    ):
        self.repository = repository
        self.history_service = history_service
        self.db = db
        self.ai_service = AIService()

    def create(
        self,
        investigation_data: InvestigationCreate,
        user_id: int,
    ) -> Investigation:
        existing = self.repository.get_by_title(
            investigation_data.title,
            user_id,
        )

        if existing:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An investigation with this title already exists.",
            )

        investigation = Investigation(
            title=investigation_data.title,
            description=investigation_data.description,
            user_id=user_id,
        )

        created = self.repository.create(investigation)

        self.history_service.create(
            InvestigationHistoryCreate(
                investigation_id=created.id,
                user_id=user_id,
                action=InvestigationAction.CREATED,
                old_value=None,
                new_value=created.title,
            )
        )

        return created



    def get_by_id(
        self,
        investigation_id: int,
        user_id: int,
    ) -> Investigation:
        investigation = self.repository.get_by_id(investigation_id)

        if investigation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investigation not found",
            )

        if investigation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investigation not found",
            )

        return investigation

    def get_all(
    self,
    user_id: int,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    status: InvestigationStatus | None = None,
):
        items = self.repository.get_all(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
        )
        total = self.repository.count(
            user_id=user_id,
            search=search,
            status=status,
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total,
        }

    def update(
    self,
    investigation_id: int,
    investigation_data: InvestigationUpdate,
    user_id: int,
) -> Investigation:

        investigation = self.get_by_id(
            investigation_id,
            user_id,
        )
        old_title = investigation.title
        old_status = investigation.status
        update_data = investigation_data.model_dump(
            exclude_unset=True
        )

        existing = None

        if "title" in update_data:
            existing = self.repository.get_by_title(
                update_data["title"],
                user_id,
            )

        if existing and existing.id != investigation.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An investigation with this title already exists.",
            )

        for key, value in update_data.items():
            setattr(investigation, key, value)

        updated = self.repository.update(investigation)

        if old_title != updated.title:
            self.history_service.create(
                InvestigationHistoryCreate(
                    investigation_id=updated.id,
                    user_id=user_id,
                    action=InvestigationAction.UPDATED,
                    old_value=old_title,
                    new_value=updated.title,
                )
            )

        if old_status != updated.status:
            self.history_service.create(
                InvestigationHistoryCreate(
                    investigation_id=updated.id,
                    user_id=user_id,
                    action=InvestigationAction.STATUS_CHANGED,
                    old_value=str(old_status),
                    new_value=str(updated.status),
                )
            )

        logger.info(
            "AI investigation completed successfully. Investigation ID=%d",
            updated.id,
        )

        return updated

    def delete(
    self,
    investigation_id: int,
    user_id: int,
):
        investigation = self.get_by_id(
        investigation_id,
        user_id,
    )
        title = investigation.title

        self.history_service.create(
            InvestigationHistoryCreate(
                investigation_id=investigation.id,
                user_id=user_id,
                action=InvestigationAction.DELETED,
                old_value=title,
                new_value=None,
            )
        )

        self.repository.delete(investigation)

        return {"message": "Investigation deleted successfully"}

    def _load_parsed_logs(
    self,
    log_file_id: int,
):
        """
        Load parsed logs for AI investigation.
        """

        parsed_logs = ParsedLogService.get_logs(
            session=self.db,
            log_file_id=log_file_id,
        )

        if not parsed_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No parsed logs found for this log file.",
            )

        return parsed_logs

    def _validate_log_file_ownership(
        self,
        log_file_id: int,
        user_id: int,
    ):
        """
        Verify that the requested log file belongs to the
        authenticated user.
        """

        log_file = LogFileRepository.get_by_id_for_user(
            session=self.db,
            log_file_id=log_file_id,
            user_id=user_id,
        )

        if log_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log file not found",
            )

        return log_file

    def _run_ai_investigation(
        self,
        investigation: Investigation,
        log_file_id: int,
        user_id: int,
    ) -> tuple[
        LangGraphInvestigationOutcome,
        dict,
    ]:
        """
        Execute the production LangGraph investigation through the
        application-wide AgentExecutionManager.
        """

        incident_summary = (
            investigation.description
            or investigation.title
        )

        manager = get_execution_manager()

        def execute_langgraph():
            return run_langgraph_investigation(
                investigation_id=investigation.id,
                user_id=user_id,
                log_file_id=log_file_id,
                incident_summary=incident_summary,
                existing_failed_component=(
                    investigation.failed_component
                ),
                existing_severity=(
                    investigation.severity
                ),
            )

        execution_result = manager.run(
            investigation_id=investigation.id,
            agent_name="langgraph_investigation",
            fn=execute_langgraph,
        )

        critical_path = manager.investigation_critical_path(
            investigation.id
        )

        if isinstance(
            execution_result,
            LangGraphInvestigationOutcome,
        ):
            outcome = execution_result

            execution_analytics = dict(
                outcome.execution_analytics or {}
            )

            execution_analytics["critical_path"] = (
                critical_path
            )

            return outcome, execution_analytics

        if isinstance(execution_result, tuple):
            outcome, execution_analytics = execution_result

            execution_analytics = dict(
                execution_analytics or {}
            )

            execution_analytics["critical_path"] = (
                critical_path
            )

            return outcome, execution_analytics

        return execution_result

    def _save_ai_results(
        self,
        investigation: Investigation,
        ai_result: AIInvestigationResponse,
        execution_analytics: dict | None = None,
    ) -> Investigation:
        """
        Save AI investigation results and execution analytics
        into the investigation record.
        """

        investigation.summary = ai_result.summary
        investigation.root_cause = ai_result.root_cause
        investigation.failed_component = ai_result.failed_component
        investigation.severity = ai_result.severity
        investigation.confidence = ai_result.confidence
        investigation.additional_notes = (
            ai_result.additional_notes
        )

        # Persist LangGraph execution analytics
        if execution_analytics is not None:
            investigation.execution_analytics = (
                execution_analytics
            )

        investigation.status = InvestigationStatus.COMPLETED

        updated = self.repository.update(
            investigation
        )

        logger.info(
            "AI investigation completed successfully. "
            "Investigation ID=%d",
            updated.id,
        )

        return updated

    def _save_validation_failed_result(
        self,
        investigation: Investigation,
        outcome: LangGraphInvestigationOutcome,
        execution_analytics: dict | None = None,
    ) -> Investigation:
        """
        Persist an investigation that completed execution but could
            not validate a root cause.
        """

        investigation.summary = outcome.summary
        investigation.root_cause = outcome.root_cause
        investigation.failed_component = outcome.failed_component
        investigation.severity = outcome.severity
        investigation.confidence = outcome.confidence
        investigation.additional_notes = outcome.additional_notes


        investigation.execution_analytics = (
            execution_analytics
            if execution_analytics is not None
            else outcome.execution_analytics
        )
        # The investigation itself completed execution successfully.
        # VALIDATION_FAILED is an AI workflow outcome, not a database
        # InvestigationStatus value.
        investigation.status = InvestigationStatus.COMPLETED

        updated = self.repository.update(
            investigation
        )

        logger.info(
            "AI investigation completed without validated root cause. "
            "Investigation ID=%d",
            updated.id,
        )

        return updated

    def run_ai_investigation(
        self,
        investigation_id: int,
        log_file_id: int,
        user_id: int,
    ) -> Investigation:
        """
        Execute a complete AI investigation.

        Workflow:
            1. Validate investigation ownership.
            2. Load parsed logs.
            3. Run AI investigation.
            4. Save AI results.
            5. Create history entry.
            6. Return updated investigation.
        """

        # Step 1: Validate investigation
        investigation = self.get_by_id(
            investigation_id=investigation_id,
            user_id=user_id,
        )
        # Step 2: Validate log-file ownership
        self._validate_log_file_ownership(
            log_file_id=log_file_id,
            user_id=user_id,
        )
        logger.info(
            "Starting AI investigation. Investigation ID=%d, Log File ID=%d",
            investigation_id,
            log_file_id,
        )
        self.history_service.create(
            InvestigationHistoryCreate(
                investigation_id=investigation.id,
                user_id=user_id,
                action=InvestigationAction.AI_INVESTIGATION_STARTED,
                old_value=None,
                new_value=None,
            )
        )

        try:
            ai_execution_result = self._run_ai_investigation(
                investigation=investigation,
                log_file_id=log_file_id,
                user_id=user_id,
                )

            if isinstance(
                    ai_execution_result,
                    tuple,
                ):
                    execution_result, execution_analytics = (
                        ai_execution_result
                    )
            else:
                    # Backward compatibility with the legacy
                    # AIInvestigationResponse contract.
                    execution_result = ai_execution_result
                    execution_analytics = {}


            # --------------------------------------------------------
            # Handle structured LangGraph outcomes.
            # --------------------------------------------------------

            if isinstance(
                    execution_result,
                    LangGraphInvestigationOutcome,
                ):
                    if execution_result.status == "VALIDATION_FAILED":

                        updated = self._save_validation_failed_result(
                            investigation=investigation,
                            outcome=execution_result,
                            execution_analytics=execution_analytics,
                        )
                        updated = self._save_validation_failed_result(
                            investigation=investigation,
                            outcome=execution_result,
                            execution_analytics=execution_analytics,
                        )

                    elif execution_result.status == "ROOT_CAUSE_VALIDATED":
                        if execution_result.result is None:
                            raise RuntimeError(
                            "Validated LangGraph outcome has no result."
                            )

                        updated = self._save_ai_results(
                            investigation=investigation,
                            ai_result=execution_result.result,
                            execution_analytics=(
                                execution_result.execution_analytics
                            ),
                        )

                    else:
                        raise RuntimeError(
                            "Unexpected LangGraph investigation outcome: "
                            f"{execution_result.status!r}"
                        )

            else:
                    # ----------------------------------------------------
                    # Legacy AIInvestigationResponse compatibility.
                    # ----------------------------------------------------
                    updated = self._save_ai_results(
                        investigation=investigation,
                        ai_result=execution_result,
                        execution_analytics=execution_analytics,
                    )

            # Step 4: Save investigation history
            self.history_service.create(
                InvestigationHistoryCreate(
                    investigation_id=updated.id,
                    user_id=user_id,
                    action=InvestigationAction.AI_INVESTIGATION_COMPLETED,
                    old_value=None,
                    new_value=updated.root_cause,
                )
            )

            return updated

        except HTTPException:
            raise

        except AIError as exc:

            logger.error(
                "AI investigation failed. "
                "Investigation ID=%d. ErrorType=%s",
                investigation_id,
                type(exc).__name__,
            )

            self.history_service.create(
                InvestigationHistoryCreate(
                    investigation_id=investigation.id,
                    user_id=user_id,
                    action=InvestigationAction.AI_INVESTIGATION_FAILED,
                    old_value=None,
                    new_value="AI investigation failed",
                )
            )

            self._mark_investigation_failed(
                investigation,
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI investigation service failed.",
            ) from exc

        except Exception as exc:

            logger.error(
                "Unexpected AI investigation failure. "
                "Investigation ID=%d. ErrorType=%s",
                investigation_id,
                type(exc).__name__,
            )

            self.history_service.create(
                InvestigationHistoryCreate(
                    investigation_id=investigation.id,
                    user_id=user_id,
                    action=InvestigationAction.AI_INVESTIGATION_FAILED,
                    old_value=None,
                    new_value="AI investigation failed",
                )
            )

            self._mark_investigation_failed(
                investigation,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI investigation failed.",
            ) from exc

    def _mark_investigation_failed(
        self,
        investigation: Investigation,
    ) -> Investigation:
        """
        Mark an investigation as failed.
        """

        investigation.status = InvestigationStatus.FAILED

        return self.repository.update(investigation)
