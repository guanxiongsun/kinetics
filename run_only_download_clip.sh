srun -p $1 --gres=gpu:6 -n1 --ntasks-per-node=1 python only_download_clip.py kinetics_code/data/kinetics-600_val_200.csv val200
