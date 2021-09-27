import os
import random
import bitops
import strutils
import asyncnet, asyncdispatch
import times

let now = times.getTime()
randomize()
let seed = convert(Seconds, Nanoseconds, now.toUnix) + now.nanosecond

proc minesGrid(mines: uint64, steps: uint64): string =
    var grid = ""
    for y in 0..7:
        grid &= "["

        for x in 0..7:
                if steps.testBit(x+y*8):
                    grid &= "Ｄ"
                elif mines.testBit(x+y*8):
                    grid &= "Ｘ"
                else:
                    grid &= "＿"

        grid &= "]\c\L"

    return grid

proc processClient(client: AsyncSocket) {.async.} =
    await client.send("=====================\c\L")
    await client.send("=== MINESLAZER 4000  \c\L")
    await client.send("=====================\c\L")

    await client.send("Use the laser to remotely detonate the mines. \c\L")
    await client.send("Make sure you don't hit any crew members with the laser though! \c\L")

    var mines = rand(uint64)
    var steps = uint64(0)
    # DEBUG
    await client.send("uint64: " & $(mines) & "\c\L")
    await client.send("uint64 hex: " & $(mines.toHex(16)) & "\c\L")
    var qwer = ""
    for i in 0..63:
        if mines.testBit(i):
            qwer &= "1"
        else:
            qwer &= "0"

    await client.send("uint64 bin: " & $(qwer) & "\c\L")
    await client.send("Solved Grid:" & "\c\L")
    await client.send(minesGrid(mines, steps))

    while true:
        await client.send("\c\L[?] Enter laser position: ")

        var x, y: int
        let line = await client.recvLine()
        if line == "":
            client.close()
            break

        try:
            let xy = line.split(",", 1)
            assert xy.len == 2

            x = parseInt(xy[0])
            y = parseInt(xy[1])

            assert x >= 0 and x < 8 and y >= 0 and y < 8

        except:
            await client.send("Wrong input.\c\L")
            continue

        await client.send(minesGrid(mines, steps))
        if not mines.testBit(x+y*8):
            await client.send("Yikes, you hit something you weren't supposed to hit.\c\L")
            await client.send("Hope you have good insurance, you're on your own.\c\L")
            await client.send(minesGrid(mines, steps))
            client.close()
            break

        steps.setBit(x+y*8)
        mines.clearBit(x+y*8)
        await client.send("Pew pew pew! Bomb successfully detonated!\c\L")
        await client.send(minesGrid(uint64(0), steps))
        
        if mines == 0:
            await client.send("\c\LWOoOOohOOOO, you've gotten rid of all mines!\c\L")
            await client.send("Here's your flag: " & getEnv("FLAG", "MagicFlag") & "\c\L")
            client.close()
            break

proc serve() {.async.} =
    var server = newAsyncSocket()
    server.setSockOpt(OptReuseAddr, true)
    server.bindAddr(Port(1234))
    server.listen()

    while true:
        let client = await server.accept()
        asyncCheck processClient(client)

asyncCheck serve()
runForever()

