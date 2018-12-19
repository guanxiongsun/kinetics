srun -p $1 --gres=cpu:4 -n1 --ntasks-per-node=1 python only_download_clip.py kinetics_code/data/kinetics-600_train.csv train
