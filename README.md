# EAI4-Babsi-Bobby-Collab
Repo made for the embedded AI course in the 4th semester of the AIS bachelor. We are working on two raspberry pi 3 which are called Babsi (Barbara) and Bobby (Robert) respectively

Team members: 

- Annalena Salchegger
- Celina Binder
- Simone Kern

Because of our venv structure make sure to use the following command to activate the venv; use the cd if you're in the repo folder since our venv is outside of it. [ergo path should be ~/Documents/EAI; else cd to go one folder up first]
```bash
cd ../
source .venv/bin/activate
```

in order to execute python files on the raspberry pi, use the following command; make sure to be in the same folder as the venv is still
```bash
python3 EAI4-Babsi-Bobby-Collab/PATH/NAME.py
```

so for example
```bash
python3 EAI4-Babsi-Bobby-Collab/Assignments/HW02/video_recording.py
```

# Setting up Babsi (or later Bobby) as a deploy key

## Generate ssh key pair on the raspberry pi via

```bash
ssh-keygen -t ed25519 -C "raspberrypi-deploy-key"
```

then add the public key to the repo as a deploy key with write access and add the private key to the ssh agent on the raspberry pi

copy private key
```bash
cat ~/.ssh/id_ed25519.pub
```

## Add deploy on github via

```Settings -> Deploy keys -> Add deploy key```

## Check ssh not https is used for the repo via

first go into the repo folder using cd

```bash
git remote -v
```

it is says https://github.com/...; WRONG

we need to change it to ssh via

```bash
git remote set-url origin git@github.com:smn-krn/EAI4-Babsi-Bobby-Collab.git
```

## Test connection via

```bash
ssh -T git@github.com
```

if it asks whether you want to continue connecting type "yes" and then it should say "Hi smn-krn/EAI4-Babsi-Bobby-Collab! You've successfully authenticated, but GitHub does not provide shell access."

## Add commit entity

For Babsi we faked an email address, so all commits added from her device are by babsi. This means we cannot differentiate here between the three of us.

```bash
git config --global user.name "Babsi"
git config --global user.email "babsi_dummyemail@raspberrypi.local"
```
