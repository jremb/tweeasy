Note: This project started 1/22/2022. It should be considered unstable and subject to significant changes in the future.

# Requirements
## Twitter API Access:
1. In order to use Twitter's API, you need to apply for a developer account at https://developer.twitter.com/. Make sure you read the TOS and use the API responsibly. 

2. At your developer dashboard, go to the Keys and Tokens tab. You'll need to generate your keys and tokens. I would recommend storing these in a password vault and not just on a file on your computer, and not just pasted into your code. 

    You should have a Consumer Key and Consumer Secret, a Bearer Token, Access Keys and Access Secret, and OAuth 2.0 Client ID and Client Secret.

3. Back on the settings tab, click on the edit button under the 'User Authentication Settings' heading. Fill this form out. The 'Callback URI / Redirect URL' can be filled in with something like `scheme://` and the 'Website URL' can just be your twitter page.

## Docker Desktop
While you don't need Docker (https://www.docker.com/) to run tweeasy, it is by far the simplest way of running it. 

Downloading Docker Desktop requires registering an account, but the personal edition is free.

You can view the Docker repository for this project here: hub.docker.com/repository/docker/jrem/tweeasy

# Quick Start:
1. Once you've downloaded Docker Desktop and installed it, all you really need from this repo is the docker-compose.yml file. You can copy and paste the contents of that file into a plain-text file on your local machine and save it with the same file name. **Change lines 14 and 29 of that file (`C:/docker_volumes/postgres_data` and `C:/docker_volumes/data`) to a path of your choosing. Without a proper volume set, your data will not persist.** The path on line 29 is where you can place tsv files in order to query multiple usernames.
3. Open a terminal with the current working directory set to the same location as your docker-compose.yml file and set your evironment variables. Your environment variables will be `POSTGRES_PASSWORD`, `TWITTER_API_BEARER`, `CONSUMER_KEY`, `CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_SECRET`. (See the section [Setting Environment Variables](https://github.com/jremb/tweeasy/blob/main/README.md#setting-environment-variables) below for some help on how to do this.)
4. In this same terminal, enter the following command:
<pre><code>docker-compose run --rm tweeasy</pre></code>

# Troubleshooting
## Invalid Interpolation Format...
If when you try to run the command `docker-compose run --rm tweeasy` you see an error message that says something like this:
<pre>invalid interpolation format for services.tweeasy.environment.[]: "required variable POSTGRES_PASSWORD is missing a value: err"</pre>
This means that you have not set the environment variables in your terminal prior to running the docker-compose command. See point 2 of the [Quick Start](https://github.com/jremb/tweeasy/blob/main/README.md#quick-start) section above and [Setting Environment Variables](https://github.com/jremb/tweeasy/blob/main/README.md#setting-environment-variables) in the [Further Help](https://github.com/jremb/tweeasy/blob/main/README.md#further-help) section below.

## Invalid Volume Specification...
If when you try to run the command `docker-compose run --rm tweeasy` you see an error message that says something like this:
<pre>Error response from daemon: invalid volume specification...</pre>
This means that you have not given a correct path in the `docker-compose.yml` file. See point 1 of the [Quick Start](https://github.com/jremb/tweeasy/blob/main/README.md#quick-start) section above.

# Further Help
## Using the Terminal/PowerShell
This isn't going to be a guide on using the Terminal or PowerShell, but there are two things you need to know to follow along with this guide. (For simplicity, I'm going to use "terminal" for both Window's PowerShell and Mac's Terminal.) 

1. When you open the terminal, it will have a 'location' or <i>current working directory</i> (cwd). This will most likely be the `path` you see before your blinking cursor when the terminal is in focus. So, on Windows, you might see `C:\Users\John`, if your Windows User account happens to be John. This means the terminal's current working directory (cwd) is <i>this</i> folder (directory). (`C:\Users\John` is the path from <i>C</i> to <i>Users</i> to <i>John</i>)

The significance of this is that when you perform certain operations in the terminal, like making a virtual environment (see below), and these operations involve creating or accessing files, these files will be created in the cwd or your terminal will try to access the files from its cwd. Thus, make sure your cwd is correct for where you want to create something or from where you access something. 

2. You can change the cwd of your terminal by typing `cd <some_path>` into the terminal and pressing enter. For example, if I wanted to go from `C:\Users\John` into my Documents folder, I could type `cd Documents` (this isn't case sensitive on Windows or Mac). If within my Documents folder I have another folder called Books then, if my cwd is `C:\Users\John\Documents`, I can just type `cd Books`. But if my cwd is `C:\Users\John` and I want to go directly to Books without typing `cd` for each directory, then I would need to type `cd ./Documents/Books`. The dot, `.`, means <i>the cwd</i>. Two dots, `..` means <i>the above directory</i>. So if you were in Books and wanted to get back to Documents, you could just type `cd ..` and your cwd would move back to Documents. 

The significance of this is that you don't want to create and access stuff through the terminal without being conscious of the terminal's cwd. When we make a virtual environment for our project, we'll want to do that with the terminal's cwd set to a folder that we've designated for that project. So you'll probably want to create a projects folder and then within that folder you can clone this repo (`git clone https://github.com/jremb/tweeasy.git`) or create whatever folder you want to store this specific project.

P.S. If you're on Windows I would suggest downloading the latest version of PowerShell (https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.2). Also, if you prefer to navigate folders through your GUI (graphical user interface) then within that folder simply right-click to bring up the context menu. From here, you should see an option that says something like  `Open in Windows Terminal` (though this may be a checkbox you need to tick when installing PowerShell). Often this is the quickest way to open PowerShell to your desired cwd. I haven't found a similar feature on Mac, but there may be one.

## Setting Environment Variables
As a brief explainer, you can think of environment variables like variables in a programming language: a box that you put things in. For example, in Python you might have the following line:

<pre><code>greeting = "Hello, world!"</code></pre>

In the example above, `greeting` is the variable or "box" that stores the value `Hello, world!`. Environment variables are like these sorts of variables, but they exist at different levels in your computer's environment(s) and not simply within a program. In the Python example, you can access the value `Hello, world!` by referencing the variable in a statement like `print(greeting)`. Likewise, you can access the value stored in an environment variable by referencing the variable name you set (but the syntax will be different depending on your terminal or shell). 

Further, environment variables, like those in a program, can be automatically deallocated in certain conditions. It's this feature that we want to take advantage of by setting our credentials as environment variables. If you open a terminal or PowerShell you can set an environment variable that exist for that session (e.g., until you close the terminal window). This can be a little inconvenient, as we will have to reassign our environment variables for each new session, but it's more secure than simply writing your credentials directly into your code.

To set environment variables:
Windows PowerShell:

<pre><code>$Env:POSTGRES_PASSWORD="example_password"</pre></code>

Mac Terminal:

<pre><code>export POSTGRES_PASSWORD="example_password"</pre></code>

Make sure `POSTGRES_PASSWORD` in your environment variable matches the one set in docker-compose.yml. Set your Twitter API credentials the same way. 

As indicated above, when you close your terminal your environment variables will no longer be set. So you will want to use this same terminal session to run the next section's instructions too.

## Accessing Your Postgres Data
The program may not seem to do anything if you're unsure of how to work with PostgreSQL. You can do this through the CLI `psql` or through a graphical user interface (GUI) like pgAdmin (https://www.pgadmin.org/). 

To use `psql`, from Docker Desktop navigate to the Containers/Apps tab, select your running container (should be a green square-stack icon named `tweeasy`) and click the drop-down arrow. There you should see another name like `tweeasy_postgres_1` and if you hover the mouse over it you will see several circle icons. The second one from the left is the CLI icon (you will see a CLI tag pop up if you hover the mouse over it). Click this and then type the following into the new window that opens:

<pre><code>
bash
psql -U postgres
</pre></code>

If you need to configure `pg_hba.conf` or `postgresql.conf` you can access these files in the directory you specified on the leftside of the colon for `volumes` in the `docker-compose.yml` file (line 14).

Note: Currently Tweeasy can display a count of table rows (this can be used to indicate how many users or followers you've queried). In the future I may add more functionality along the lines of viewing data, but that's really not the intention of the program. The intention is to provide an easy way for people to make use of some basic features of the Twitter API with the Tweepy module to *get* data.
