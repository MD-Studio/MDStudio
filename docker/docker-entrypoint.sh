echo 'Running installer' &>> docker/.INSTALLING

if [ ! -d lie_venv/ ]; then
    bash installer.sh --setup --local-dev &>> docker/.INSTALLING
fi

echo 'Enabling debugging code' &>> docker/.INSTALLING
# disable the debugger disabling code which spews a LOT of warnings
sed -i 's/ sys.settrace(None)/ #sys.settrace(None)/g' /app/lie_venv/lib/python2.7/site-packages/twisted/internet/process.py

echo "source /app/lie_venv/bin/activate" >> ~/.bashrc
echo "export MONGO_HOST=mongo" >> ~/.bashrc
echo "export IS_DOCKER=1" >> ~/.bashrc

echo 'Compiling pycharm helpers' &>> docker/.INSTALLING
if [ -d /app/.pycharm_helpers/pydev/ ]; then
    python /app/.pycharm_helpers/pydev/setup_cython.py build_ext --inplace &>> docker/.INSTALLING
fi

echo 'Install IDE bindings' &>> docker/.INSTALLING
# make sure we have the bindings for our IDE
pip install -r /app/data/python_default_requirements.txt &>> docker/.INSTALLING

echo 'Install NPM packages' &>> docker/.INSTALLING
mkdir -p /app/app/node_modules
npm install --prefix /app/app --unsafe-perm &>> docker/.INSTALLING

# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

#execute the default phusion script
/sbin/my_init