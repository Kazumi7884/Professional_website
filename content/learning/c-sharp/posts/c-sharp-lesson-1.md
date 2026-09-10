---
title: C# Lesson 1
description: Early C# lesson notes and key takeaways.
date: '2026-06-05'
lastmod: '2026-07-15'
aliases:
- /learning/c-sharp/posts/c-sharp-lesson-1.html
- /posts/c-sharp-lesson-1/
- /posts/c-sharp-lesson-1.html
tags:
- learning
- c sharp
- post
searchable: true
legacy_path: learning/c-sharp/posts/c-sharp-lesson-1.html
categories:
- Dev log
entryType: "post"
---

**Goal:** Document early learning progress in C#.

**Current focus:** Console input/output and simple class design.

## What I studied

- `Console.WriteLine()`
- Code comments
- `Console.ReadKey()`
- Variables

## Practice task

Using Visual Studio, I created a .NET 8 console app. The exercise covered disabling top-level statements, adding code comments with `//`, and changing the original `Console.WriteLine("Hello World!")` output to a custom greeting.

## Starter snippet

```csharp
Console.WriteLine("Hello Kaz!");
```

## Without top-level statements

```csharp
namespace Lesson_1_Hello_World
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, Kaz!");
        }
    }
}
```

## Variables practice

I then added a `myFriendsName` variable and used Visual Studio autocomplete to wire it into the console output.

```csharp
// See https://aka.ms/new-console-template for more information
Console.WriteLine("Hello, Kaz!");

// declare a string variable named myFriendsName
string myFriendsName;
myFriendsName = "John";
Console.WriteLine(myFriendsName);

// wait for user input before closing the console window
Console.ReadKey();
```

## What I will do next

- Continue into [C# Lesson 2](/learning/c-sharp/posts/c-sharp-lesson-2/).
- Keep the wider [C# posts index](/learning/c-sharp/posts/) updated as new lessons are added.

[Back to C#](/learning/c-sharp/)
[C# posts](/learning/c-sharp/posts/)
