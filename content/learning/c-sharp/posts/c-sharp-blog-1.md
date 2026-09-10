---
title: 'Blog 1: The Console Apps Overview and Examples'
description: Hello World, calculator basics, if statements, and switch statements.
date: '2026-06-05'
lastmod: '2026-06-05'
aliases:
- /learning/c-sharp/posts/c-sharp-blog-1.html
- /posts/c-sharp-blog-1/
- /posts/c-sharp-blog-1.html
tags:
- learning
- c sharp
- post
searchable: true
legacy_path: learning/c-sharp/posts/c-sharp-blog-1.html
categories:
- Dev log
entryType: "post"
---

10/05/24

## What is a "Console" App and Why Use It?

Console apps are applications that make use of the Windows Terminal.
This can be a Command Prompt, PowerShell Terminal, DOS interface, or
other similar programs. They are particularly useful for tasks
requiring text-based interaction or automation, such as system
administration, data processing, and testing.

Developers often use console apps for prototyping, debugging, and
learning purposes. They provide a lightweight and straightforward
environment for experimenting with code snippets or implementing
simple utilities.

## How I've Incorporated This:

In my recent project, I utilized console apps to automate repetitive
tasks in data analysis. By leveraging the simplicity and flexibility
of console-based interfaces, I streamlined data processing
workflows, reducing manual effort and increasing productivity. By
utilising the console windows I've been able to create basic outputs
for my needs, these windows can come from different files but
typically on a Windows install will default to a Command Prompt or a
CMD window, although PowerShell is also used.

![Example of console output from a basic command-line program.](/assets/images/csharp/blog-1/console-output-example.webp)

Example console output (from my C# learning notes).

The following is an example code using a batch file which will
perform basic Windows repairs.

```
@echo off

rem this is system file check
rem pause pauses the program to make you put a keystroke in to continue
rem like how you pause and unpause a game
sfc /scannow
pause

rem this is deployment image servicing and management
rem basically does an online check with Microsoft's database
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth
pause

rem chkdsk is check disk
rem delete until it matches the drives you have
chkdsk /f /b /perf /scan c:
pause

rem this defrags all hdd's you have at normal priority instead of low thanks to /c and /h
defrag /c /u /v /x /h
pause
cleanmgr.exe /autoclean
cleanmgr.exe /d c /verylowdisk

exit
rem exit exits the program
rem v2.0 - added defrag capability
rem v3.0 added disk cleanup capability
```

By using this, Windows is using SFC which is a System File Check,
DISM which is Deployment Image Servicing and Management and CHKDSK
which is a Check Disk. SFC scans the current Windows system for
corrupted files and then download and replace any files found to be
corrupted.

[Back to C#](/learning/c-sharp/)
