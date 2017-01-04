if [ ! -d lie_venv/ ]; then
    bash installer.sh --setup --local-dev &>> docker/.INSTALLING
else
    bash installer.sh --upgrade &>> docker/.INSTALLING
fi

echo "source /app/lie_venv/bin/activate" >> ~/.bashrc

if [ -d /app/.pycharm_helpers/pydev/ ]; then
    python /app/.pycharm_helpers/pydev/setup_cython.py build_ext --inplace &>> docker/.INSTALLING
fi

# make sure we have the bindings for our IDE
# pip install -r /app/data/python_default_requirements.txt

# notify the installation has been completed
echo '<<<<COMPLETED>>>>' >> docker/.INSTALLING

#execute the default phusion script
/sbin/my_init