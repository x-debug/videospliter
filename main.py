import os
import json
import click
import webvtt
import datetime
import time
from datetime import datetime as dt
from webvtt.writers import WebVTTWriter
from moviepy.editor import VideoFileClip


@click.group()
def cli():
    pass


def convert_to_seconds(s):
    x = time.strptime(s.split('.')[0], '%H:%M:%S')
    return datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()


def convert_to_timedelta(s):
    x = time.strptime(s, '%H:%M:%S.%f')
    ms = dt.strptime(s, '%H:%M:%S.%f')
    return datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec, microseconds=ms.microsecond)


def convert_to_dt(s):
    return dt.strptime(s, '%H:%M:%S.%f')


def convert_to_str(s):
    return dt.strftime(s, '%H:%M:%S.%f')[:-3]


def substract_time(s, t):
    x = convert_to_dt(s)
    y = convert_to_timedelta(t)
    return convert_to_str(x - y)


def add_time(s, t):
    x = convert_to_dt(s)
    y = convert_to_timedelta(t)
    return convert_to_str(x + y)


def write_file(fname, captions, baseTime='00:00:00.000'):
    with open(fname, 'wt+') as f:
        writer = WebVTTWriter()
        for caption in captions:
            start = substract_time(caption.start, baseTime)
            end = substract_time(caption.end, baseTime)
            caption.start = start
            caption.end = end
        writer.write(captions, f)
        f.flush


@cli.command()
@click.option('--vtt', prompt='Your vtt file', help='The vtt file of the video')
@click.option('--video', prompt='Your video file', help='The video file to split')
@click.option('--output', prompt='Your output folder', help='The output folder', default='./')
@click.option('--duration', prompt='Your duration(minutes)', help='The duration of the split', default=2, type=int)
def split_video(vtt, video, output='./', duration=2):
    """Simple program that split a video based on a vtt file"""

    if output[-1] != '/':
        output = output + '/'

    if os.path.exists(output) is False:
        os.mkdir(output)

    duration = duration * 60  # seconds
    input_video = VideoFileClip(video)
    click.echo('Splitting the video %s based on the vtt file %s' %
               (video, vtt))

    frames = input_video.fps
    start_clip = '00:00:00.000'
    end_clip = '00:00:00.000'
    base_time = '00:00:00.000'
    step_seconds = 0
    step_captions = []
    num = 0
    clips = []
    for caption in webvtt.read(vtt):
        # if step_seconds == 0:
        #     start_clip = caption.start

        start = convert_to_seconds(caption.start)
        end = convert_to_seconds(caption.end)

        span = end - start
        step_seconds = step_seconds + span
        step_captions.append(caption)

        if step_seconds >= duration:
            base_time = end_clip
            end_clip = caption.end
            num += 1
            input_video.subclip(start_clip, end_clip).write_videofile(
                output + f'clip{num}' + '.mp4',
                fps=frames,
                # bitrate="4000k",
                # threads=1,
                # preset='ultrafast',
                # codec='h264'
            )
            click.echo('Start: %s, End: %s, BaseTime: %s, Text: %s' %
                       (start_clip, end_clip, base_time, caption.text))
            click.echo(
                f'StartClip: {step_captions[0].start}, EndClip: {step_captions[-1].end}')
            write_file(output + f'clip{num}.vtt', step_captions, base_time)
            clips.append({
                'vtt': f'clip{num}.vtt',
                'video': f'clip{num}' + '.mp4'
            })
            step_captions = []
            step_seconds = 0
            start_clip = end_clip

    if step_seconds > 0:
        base_time = end_clip
        end_clip = caption.end
        num += 1
        input_video.subclip(start_clip, end_clip).write_videofile(
            output + f'clip{num}' + '.mp4',
            fps=frames,
            # bitrate="4000k",
            # threads=1,
            # preset='ultrafast',
            # codec='h264'
        )
        step_captions.append(caption)
        click.echo('Start: %s, End: %s, BaseTime: %s, Text: %s' %
                   (start_clip, end_clip, base_time, caption.text))
        click.echo(
            f'StartClip: {step_captions[0].start}, EndClip: {step_captions[-1].end}')
        write_file(output + f'clip{num}.vtt', step_captions, base_time)
        clips.append({
            'vtt': f'clip{num}.vtt',
            'video': f'clip{num}' + '.mp4'
        })
    with open(output + 'clips.json', 'wt+') as f:
        f.write(json.dumps(clips, indent=True))


if __name__ == '__main__':
    cli()
