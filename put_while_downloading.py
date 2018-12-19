import argparse
import json
import os
import ftplib
from joblib import delayed
from joblib import Parallel

def FTP_wrapper():
    ftp = ftplib.FTP()
    ftp.connect ("10.107.1.68")
    ftp.login ("sunguanxiong", "Sgx19940210")
    return ftp

def upload_video(video_name, download_dir, remote_dir, ftp):
    video_file = os.path.join(download_dir, video_name)

    status = False
    # Putting the video to remote directory.
    cmd = "STOR " + video_name
    try:
        status = os.path.exists(video_file)
        with open(video_file, 'rb') as f:
            ftp.storbinary(cmd, f)
    except:
        return tuple([video_name, status, "err"])
    
    os.remove(video_file)
    return tuple([video_name, status, 'Uploaded'])


def main(download_dir, remote_dir, num_jobs=24):
    """
    arguments:
    ---------
    download_dir: str
        Directory of the downloaded videos
    remote_dir: str
        Remote directory to store videos
    num_jobs: num
        Number of processes.
    """
    # Loop until no videos
    
    ftp = FTP_wrapper()
    ftp.cwd(remote_dir)
    # upload 100 videos every time
    buffer = 100
    video_list = os.listdir(download_dir)[:100]
    while video_list:
        if num_jobs == 1:
            status_lst = []
            for video in video_list:
                print(video)
                status_lst.append(upload_video(video, download_dir, remote_dir, ftp))
        else:
            status_lst = Parallel(n_jobs=num_jobs)(delayed(upload_video)(video, download_dir, remote_dir, ftp) for video in video_list)

    # Save download report.
    with open('upload_report.json', 'w') as fobj:
        fobj.write(json.dumps(status_lst))


if __name__ == '__main__':
    description = 'Helper script for uploading while downloading videos'
    p = argparse.ArgumentParser(description=description)
    p.add_argument('download-dir', type=str,
                   help=('The directory for downloaded videos'))
    p.add_argument('remote_dir', type=str,
                   help='Remote directory where videos will be uploaded.')
    p.add_argument('-n', '--num-jobs', type=int, default=8)

    main(**vars(p.parse_args()))