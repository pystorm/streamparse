Java Cookbook Issues
=======================
This file documents the steps necessary to report and issue with the Java cookbook. Following these guidelines will help ensure your issue is resolved in a timely manner.

Reporting
---------
When you report an issue, please include the following information:

- A high-level overview of what you are trying to accomplish
- An [SSCCE](http://sscce.org/) _Short, Self Contained, Correct (Compilable), Example_
- The command you ran
- What you expected to happen
- What actually happened
- The exception backtrace(s), if any
- What operating system and version
- Everything output by running `env`
- What version of the cookbook are you using?
- What version of Ruby you are using (run `ruby -v`)
- What version of Rubygems you are using (run `gem -v`)
- What version of Chef you are using (run `knife -v`)

Here's a snippet you can copy-paste into the issue and fill out:

```text
(What is the issue? What are you trying to do? What happened?)

- Command: `...`
- OS:
- Cookbook Version:
- Ruby Version:
- Rubygems Version:
- Chef Version:
- env:
    ```text
    # Paste your env here
    ```
- Backtrace:
    ```text
    # Paste backtrace here
    ```
```

[Create a ticket](https://github.com/agileorbit-cookbooks/java/issues/new) describing your problem and include the information above.
