rm -rf apps/_default/databases
rm -rf CSE_183_Group_10_Project
rm CSE_183_Group_10_Project.zip
py4web run --errorlog=:stdout -L 20 apps
