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

def download_video(video_name, download_dir, remote_dir, ftp):
    video_file = os.path.join(download_dir, video_name)

    status = False
    # Putting the video to remote directory.
    cmd = "RETR " + video_name
    try:
        with open(video_file, 'wb') as f:
            ftp.retrbinary(cmd, f.write)
    except:
        print("errrrrrrrrrrr!!!!")
        return tuple([video_name, status, "err"])

    ftp.delete(video_name)
    return tuple([video_name, status, 'Downloaded'])


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
    video_list = ftp.nlst()[:10]
    print (video_list)
    while video_list:
        if num_jobs == 1:
            status_lst = []
            for video in video_list:
                print(video)
                status_lst.append(download_video(video, download_dir, remote_dir, ftp))
        else:
            status_lst = Parallel(n_jobs=num_jobs)(delayed(download_video)(
                video, download_dir, remote_dir, ftp) for video in video_list)

    # Save download report.
    with open('download_report.json', 'w') as fobj:
        fobj.write(json.dumps(status_lst))


if __name__ == '__main__':
    description = 'Helper script for uploading while downloading videos'
    p = argparse.ArgumentParser(description=description)
    p.add_argument('remote_dir', type=str,
                   help=('The directory for downloaded videos'))
    p.add_argument('download_dir', type=str,
                   help='Remote directory where videos will be uploaded.')
    p.add_argument('-n', '--num-jobs', type=int, default=1)

    main(**vars(p.parse_args()))
