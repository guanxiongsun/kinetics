import argparse
import glob
import json
import os
import shutil
import subprocess
import uuid
from collections import OrderedDict

from joblib import delayed
from joblib import Parallel
import pandas as pd
import time


def create_video_folders(dataset, output_dir, tmp_dir):
    """Creates a directory for each label name in the dataset."""
    """if 'label-name' not in dataset.columns:
        this_dir = os.path.join(output_dir, 'test')
        if not os.path.exists(this_dir):
            os.makedirs(this_dir)
        # I should return a dict but ...
        return this_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir) """

    label_to_dir = {}
    for label_name in dataset['label-name'].unique():
        # this_dir = os.path.join(output_dir, label_name)
        this_dir = output_dir
        if not os.path.exists(this_dir):
            os.makedirs(this_dir)
        label_to_dir[label_name] = this_dir
    return label_to_dir


def construct_video_filename(row, label_to_dir, trim_format='%06d'):
    """Given a dataset row, this function constructs the
       output filename for a given video.
    """
    basename = '%s_%s_%s_%s.mp4' % (row['video-id'], row['label-name'],
                                 trim_format % row['start-time'],
                                 trim_format % row['end-time'])
    if not isinstance(label_to_dir, dict):
        dirname = label_to_dir
    else:
        dirname = label_to_dir[row['label-name']]
    # output_filename = os.path.join(dirname, basename)
    output_filename = os.path.join(dirname, basename)
    #print (output_filename)
    return output_filename


def download_clip(ind, video_identifier, output_filename,
                  start_time, end_time,
                  tmp_dir='/tmp/kinetics',
                  num_attempts=5,
                  url_base='https://www.youtube.com/watch?v='):
    """Download a video from youtube if exists and is not blocked.

    arguments:
    ---------
    video_identifier: str
        Unique YouTube video identifier (11 characters)
    output_filename: str
        File path where the video will be stored.
    start_time: float
        Indicates the begining time in seconds from where the video
        will be trimmed.
    end_time: float
        Indicates the ending time in seconds of the trimmed video.
    """
    # Defensive argument checking.
    assert isinstance(video_identifier, str), 'video_identifier must be string'
    assert isinstance(output_filename, str), 'output_filename must be string'
    assert len(video_identifier) == 11, 'video_identifier must have length 11'

    status = False
    # Construct command line for getting the direct video link.
    # tmp_filename = os.path.join(tmp_dir,
    #                            '%s.%%(ext)s' % uuid.uuid4())
    # start_d = time.time()
    # print(str(ind)+" downloading ......")
    # # print(str(ind)+" -> downloading ......")
    # command = ['youtube-dl',
    #            '--quiet', '--no-warnings',
    #            '-f', 'mp4',
    #            '-o', '"%s"' % output_filename,
    #            '"%s"' % (url_base + video_identifier)]
    # command = ' '.join(command)
    # attempts = 0
    # while True:
    #     try:
    #         output = subprocess.check_output(command, shell=True,
    #                                          stderr=subprocess.STDOUT)
	#     end_d = time.time()
	#     # print(str(ind)+" - downloaded <-")
    #     except subprocess.CalledProcessError as err:
    #         attempts += 1
    #         if attempts == num_attempts:
    #             return status, err.output
	# 	print(str(ind)+" ! download errorrrrrrr !!!!!!!!!!!!")
    #     else:
    #         break

    # tmp_filename = glob.glob('%s*' % tmp_filename.split('.')[0])[0]
    # Construct command to trim the videos (ffmpeg required).

    print(str(ind)+" -> ffmpeging ......")
    ### filename is ZZfmdYrlBf4_acting in play_000184_000194.mp4
    ### new_basename = os.path.basename(output_filename).split('.')[0] + "_new.mp4"

    new_basename = os.path.basename(output_filename).split('.')[0] + ".mp4"

    ### change filename to v_label_xxx.avi
    name_id = new_basename[:11] # save youtube-id
    new_basename = new_basename[12:]
    name_parts = new_basename.split('_')

    # new_basename = v  _      label       _      id       _  xxxxxxxxxx.mp4
    new_basename = "v_" + name_parts[0] + "_" + name_id + "_" + name_parts[1] + name_parts[2]
    print(new_basename)
    new_dirname = os.path.dirname(output_filename).split('/')[0] + "_new"
    new_output_filename = os.path.join(new_dirname, new_basename)
    # print("output_filename - "+output_filename)
    # print("new_output_file - "+ new_output_filename)
    start_f = time.time()
    command = ['ffmpeg',
               '-i', '"%s"' % output_filename,
               '-ss', str(start_time),
               '-t', str(end_time - start_time),
               '-c:v', 'libx264', '-c:a', 'copy',
               '-threads', '1',
               '-loglevel', 'panic',
               '"%s"' % new_output_filename]
    command = ' '.join(command)
    try:
        output = subprocess.check_output(command, shell=True,stderr=subprocess.STDOUT)
        end_f = time.time()
        print(str(ind)+" - ffmpeged <-")
    except subprocess.CalledProcessError as err:
        print(str(ind)+" ! ffmpeg errorrrrrrrrrrrrr !!!!!!!!!!")
        return status, err.output

    # Check if the video was successfully saved.
    #start_r=time.clock()
    status = os.path.exists(new_output_filename)
    # os.remove(tmp_filename)
    # end_r = time.clock()
    # print("remove used: "+str(end_r-start_r))
    # print (str(ind)+" successfull - download used: "+ str(end_d - start_d) + " s, ffmpeg used: "+str(end_f - start_f)+" s")
    print (str(ind)+" successfull - ffmpeg used: "+ str(end_f - start_f) + " s")
    return status, 'Downloaded'


def download_clip_wrapper(ind, row, label_to_dir, trim_format, tmp_dir):
    """Wrapper for parallel processing purposes."""
    output_filename = construct_video_filename(row, label_to_dir,
                                               trim_format)
    clip_id = os.path.basename(output_filename).split('.mp4')[0]

    # if os.path.exists(output_filename):
    #     status = tuple([clip_id, True, 'Exists'])
    #     return status

    downloaded, log = download_clip(ind, row['video-id'], output_filename,
                                    row['start-time'], row['end-time'],
                                    tmp_dir=tmp_dir)
    status = tuple([clip_id, downloaded, log])
    return status


def parse_kinetics_annotations(input_csv, ignore_is_cc=False):
    """Returns a parsed DataFrame.

    arguments:
    ---------
    input_csv: str
        Path to CSV file containing the following columns:
          'YouTube Identifier,Start time,End time,Class label'

    returns:
    -------
    dataset: DataFrame
        Pandas with the following columns:
            'video-id', 'start-time', 'end-time', 'label-name'
    """
    df = pd.read_csv(input_csv)
    if 'youtube_id' in df.columns:
        columns = OrderedDict([
            ('youtube_id', 'video-id'),
            ('time_start', 'start-time'),
            ('time_end', 'end-time'),
            ('label', 'label-name')])
        df.rename(columns=columns, inplace=True)
        if ignore_is_cc:
            df = df.loc[:, df.columns.tolist()[:-1]]
    return df


def main(input_csv, output_dir,
         trim_format='%06d', num_jobs=24, tmp_dir='/tmp/kinetics',
         drop_duplicates=False):

    # Reading and parsing Kinetics.
    dataset = parse_kinetics_annotations(input_csv)
    # if os.path.isfile(drop_duplicates):
    #     print('Attempt to remove duplicates')
    #     old_dataset = parse_kinetics_annotations(drop_duplicates,
    #                                              ignore_is_cc=True)
    #     df = pd.concat([dataset, old_dataset], axis=0, ignore_index=True)
    #     df.drop_duplicates(inplace=True, keep=False)
    #     print(dataset.shape, old_dataset.shape)
    #     dataset = df
    #     print(dataset.shape)

    # Creates folders where videos will be saved later.
    label_to_dir = create_video_folders(dataset, output_dir, tmp_dir)

    # Download all clips.
    start = time.time()
    print("num_jobs="+str(num_jobs))
    if num_jobs == 1:
        status_lst = []
        for i, row in dataset.iterrows():
            print(i)
            status_lst.append(download_clip_wrapper(i, row, label_to_dir,
                                                    trim_format, tmp_dir))
    else:
        status_lst = Parallel(n_jobs=num_jobs)(delayed(download_clip_wrapper)(i,
            row, label_to_dir,
            trim_format, tmp_dir) for i, row in dataset.iterrows())

    end = time.time()
    print("TOTAL USED: "+str(end-start)+" s......")
    # Clean tmp dir.
    # shutil.rmtree(tmp_dir)

    # Save download report.
    with open('download_report.json', 'w') as fobj:
        fobj.write(json.dumps(status_lst))


if __name__ == '__main__':
    description = 'Helper script for downloading and trimming kinetics videos.'
    p = argparse.ArgumentParser(description=description)
    p.add_argument('input_csv', type=str,
                   help=('CSV file containing the following format: '
                         'YouTube Identifier,Start time,End time,Class label'))
    p.add_argument('output_dir', type=str,
                   help='Output directory where videos will be saved.')
    p.add_argument('-f', '--trim-format', type=str, default='%06d',
                   help=('This will be the format for the '
                         'filename of trimmed videos: '
                         'videoid_%0xd(start_time)_%0xd(end_time).mp4'))
    p.add_argument('-n', '--num-jobs', type=int, default=256)
    p.add_argument('-t', '--tmp-dir', type=str, default='/tmp/kinetics')
    p.add_argument('--drop-duplicates', type=str, default='non-existent',
                   help='Unavailable at the moment')
                   # help='CSV file of the previous version of Kinetics.')
    main(**vars(p.parse_args()))
