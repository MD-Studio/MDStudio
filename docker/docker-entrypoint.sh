if [ ! -d lie_venv/ ]; then
    bash installer.sh --setup --local-dev &>> docker/.INSTALLING
else
    bash installer.sh --setup --local-dev &>> docker/.INSTALLING
fi

# disable the debugger disabling code which spews a LOT of warnings
sed -i 's/ sys.settrace(None)/ #sys.settrace(None)/g' /app/lie_venv/lib/python2.7/site-packages/twisted/internet/process.py

echo "source /app/lie_venv/bin/activate" >> ~/.bashrc
echo "export MONGO_HOST=mongo" >> ~/.bashrc
echo "export IS_DOCKER=1" >> ~/.bashrc

if [ -d /app/.pycharm_helpers/pydev/ ]; then
    python /app/.pycharm_helpers/pydev/setup_cython.py build_ext --inplace &>> docker/.INSTALLING
fi

# make sure we have the bindings for our IDE
pip install -r /app/data/python_default_requirements.txt &>> docker/.INSTALLING

cd /app/app 
npm install --unsafe-perm &>> /app/docker/.INSTALLING
cd /app/  

# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

#execute the default phusion script
/sbin/my_init