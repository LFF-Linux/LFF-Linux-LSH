**LFF Linux Shell (LSH)**

LSH is a custom shell I built for my Linux OS project, LFF Linux. That said, it should work on any Debian-based Linux system with Python installed (tested on Ubuntu 24.04).
Much like Bash, LSH lets you run system commands and can even serve as a login shell. It also includes a built-in package manager (also called lpm), which installs packages from my GitHub organization: LFF-Linux-Packages (https://github.com/LFF-Linux-Packages).
I occasionally create and publish new packages for it, and plan to expand the ecosystem as LFF Linux evolves.

**How to install (The easy way)**

1. Download the deb from https://github.com/LFF-Linux/LFF-Linux-LSH/releases/latest
2. Open the file in your software/package manager
3. Install the package, following the instructions from the software/package manager

**How to set as login shell (The easy way pt. 2)**

Just run the commmand <pre> ```chsh /usr/bin/lsh $USER && rm ~/.profile && echo "exec /usr/bin/lsh" > ~/.profile ``` </pre>

Your all done! The next time you log in using tty or open a terminal, lsh will greet you! If you have any issues, feel free to put them in the issues page of this repository!

**How to install (The hard way)**

1. Download the latest release from https://github.com/LFF-Linux/LFF-Linux-LSH/releases/latest
2. Open a terminal, and go to the folder that contains the *lsh.py* file.
3. Run the command <pre> ```sudo cp ./lsh.py /usr/bin/lsh && sudo chmod 777 /usr/bin/lsh ``` </pre>
4. Run the command <pre> ```lsh --version ``` </pre> if it outputs the version you downloaded, your good to go!
5. Run the command <pre> ```lsh ``` </pre> to enter your new shell!

**How to set as login shell (The hard way pt. 2)**

Warning: This script is experimential and it is not recommended to set it as the login/default shell.

1. Run the command <pre> ```sudo echo "/usr/bin/lsh" > /etc/shells && chsh /usr/bin/lsh $USER && rm ~/.profile && echo "exec /usr/bin/lsh" > ~/.profile ``` </pre>

Your all done! The next time you log in using tty or open a terminal, lsh will greet you! If you have any issues, feel free to put them in the issues page of this repository!
