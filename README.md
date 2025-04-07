# LFF Linux Shell (LSH)

LSH is a custom shell I built for my Linux OS project, LFF Linux. That said, it should work on any Debian-based Linux system with Python installed (tested on Ubuntu 24.04).  
Much like Bash, LSH lets you run system commands and can even serve as a login shell. It also includes a built-in package manager (called `lpm`), which installs packages from my GitHub organization: [LFF-Linux-Packages](https://github.com/LFF-Linux-Packages).  
I occasionally create and publish new packages for it, and plan to expand the ecosystem as LFF Linux evolves.

---

## How to install (The easy way)

1. Download the deb from the [latest LSH release](https://github.com/LFF-Linux/LFF-Linux-LSH/releases/latest).  
2. Open the file in your software/package manager.  
3. Install the package, following the instructions from the software/package manager.

## How to set as login shell (The easy way)

> **Warning:** This script is experimental and it is *not* recommended to set it as the login/default shell.

Run the command:
```bash
chsh --shell /usr/bin/lsh $USER && \
rm ~/.profile && \
echo "exec /usr/bin/lsh" > ~/.profile
```

You're all done! The next time you log in using **TTY** or open a terminal, **LSH** will greet you!  
If you have any issues, feel free to report them **on the issues page** of this repository.

---

## How to install (The hard way)

1. Download the [latest LSH release](https://github.com/LFF-Linux/LFF-Linux-LSH/releases/latest).  
2. Open a terminal and go to the folder that contains the *lsh.py* file.  
3. Run the command:
```bash
sudo cp ./lsh.py /usr/bin/lsh && \
sudo chmod 777 /usr/bin/lsh
```
4. Run `lsh --version`. If it outputs the version you downloaded, you're good to go!  
5. Run `lsh` to enter your new shell!

## How to set as login shell (The hard way)

> **Warning:** This script is experimental and it is *not* recommended to set it as the login/default shell.

Run the command:
```bash
sudo echo "/usr/bin/lsh" > /etc/shells && \
chsh --shell /usr/bin/lsh $USER && \
rm ~/.profile && \
echo "exec /usr/bin/lsh" > ~/.profile
```

You're all done! The next time you log in using **TTY** or open a terminal, **LSH** will greet you!  
If you have any issues, feel free to report them **on the issues page** of this repository.
