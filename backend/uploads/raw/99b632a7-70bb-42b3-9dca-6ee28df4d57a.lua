print('^4-----------------------------------------')
print('^4LOGS MADE BY LAZOS FOR FURIUS DEVELOPMENT')
print('^4-----------------------------------------')

ESX = nil

TriggerEvent('esx:getSharedObject', function(obj) ESX = obj end)

AddEventHandler('playerConnecting', function(t,t2,t3)
    local source = source
    local identifier = GetPlayerIdentifier(source)
    local name = GetPlayerName(source)
    local playerIp = GetPlayerEndpoint(source)
    local playerPing = GetPlayerPing(source)

    PerformHttpRequest('YOUR_WEBHOOK', function(err, text, headers) end, 'POST', json.encode({embeds={{title="__**Join Logs**__",description="\nPlayer name: "..name.. "`\nIdentifier: "..identifier.. "\nPlayer Ping: "..playerPing.. "\nReason: Μόλις  έκανε join",color=16711680}}}), { ['Content-Type'] = 'application/json' })
end)

AddEventHandler('playerDropped', function(reason)
    local lPlayer = ESX.GetPlayerFromId(source)

    if lPlayer then
        local identifier = lPlayer.identifier
        local name = GetPlayerName(source)
        local playerIp = GetPlayerEndpoint(source)
        local playerPing = GetPlayerPing(source)

        PerformHttpRequest('YOUR_WEBHOOK', function(err, text, headers) end, 'POST', json.encode({embeds={{title="__**Leave Logs**__",description="\nPlayer name: "..name.. "`["..source.."]`\nIdentifier: "..identifier.. "\nPlayer Ping: "..playerPing.. "\nReason: "..reason.."",color=16711680}}}), { ['Content-Type'] = 'application/json' })
    else
        print('^7 Player Disconnected On Loading Screen')
    end
end)

AddEventHandler('chatMessage', function(source, name, message)
    PerformHttpRequest('YOUR_WEBHOOK', function(err, text, headers) end, 'POST', json.encode({embeds={{title="__**Chat Logs**__",description="\nPlayer name: "..name.. "`["..source.."]`\nType: "..message.."",color=16711680}}}), { ['Content-Type'] = 'application/json' })
end)

RegisterServerEvent('lz-logs:aimlogs')
AddEventHandler('lz-logs:aimlogs', function(pedId)
    local name,id = GetPlayerName(source), ESX.GetPlayerFromId(source)
    local tname,tid = GetPlayerName(pedId), ESX.GetPlayerFromId(pedId)

    PerformHttpRequest('YOUR_WEBHOOK', function(err, text, headers) end, 'POST', json.encode({embeds={{title="__**Aim Logs**__",description="\nPlayer name: "..name.. "`["..id.source.."]`\nIs aiming: "..tname.." `["..tid.source.."]`",color=16711680}}}), { ['Content-Type'] = 'application/json' })
end)

RegisterServerEvent('lz-logs:killlogs')
AddEventHandler('lz-logs:killlogs', function(message, weapon)
    local time = os.date('*t')
    local hour = time.hour-2

    PerformHttpRequest('YOUR_WEBHOOK', function(err, text, headers) end, 'POST', json.encode({embeds={{title="__**Kill Logs**__",description="\n"..message.. "\nWeapon: "..weapon.."\nTime: "..hour..":"..time.min,color=16711680}}}), { ['Content-Type'] = 'application/json' })
end)