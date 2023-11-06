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
        f.flush()


def clip_num(label, n):
    return f'{label}{n:02d}'


@cli.command()
@click.option('--video', prompt='Your video file', help='The video file to split')
@click.option('--vtt', prompt='Your vtt file', help='The vtt file of the video', default='')
@click.option('--output', prompt='Your output folder', help='The output folder', default='./')
@click.option('--duration', prompt='Your duration(minutes)', help='The duration of the split', default=2, type=int)
def split_video(video, vtt='', output='./', duration=2):
    """Simple program that split a video based on a vtt file"""

    if output[-1] != '/':
        output = output + '/'

    if os.path.exists(output) is False:
        os.mkdir(output)

    duration = duration * 60  # seconds
    input_video = VideoFileClip(video)

    if vtt == '':
        clips = []
        num = 0
        startSeconds = 0
        endSeconds = startSeconds + duration
        while endSeconds < input_video.duration:
            num += 1
            input_video.subclip(startSeconds, endSeconds).write_videofile(
                output + clip_num('clip', num) + '.mp4',
                fps=input_video.fps,
            )
            startSeconds = endSeconds
            endSeconds = startSeconds + duration
            clips.append({
                'video': clip_num('clip', num) + '.mp4',
                'seconds': duration
            })

        input_video.subclip(startSeconds, input_video.duration).write_videofile(
            output + clip_num('clip', num) + '.mp4',
            fps=input_video.fps,
        )
        clips.append({
            'video': clip_num('clip', num) + '.mp4',
            'seconds': duration
        })
        with open(output + 'clips.json', 'wt+') as f:
            f.write(json.dumps(clips, indent=True))
        return

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
        start = convert_to_seconds(caption.start)
        end = convert_to_seconds(caption.end)

        span = end - start
        step_seconds = step_seconds + span
        step_captions.append(caption)

        if step_seconds >= duration:
            base_time = end_clip
            end_clip = caption.end
            num += 1
            # 在创建视频剪辑时，考虑到视频和字幕可能存在的时间差
            start_time = convert_to_seconds(start_clip)
            end_time = convert_to_seconds(end_clip)
            input_video.subclip(start_time, end_time).write_videofile(
                output + clip_num('clip', num) + '.mp4',
                fps=frames,
            )
            click.echo('Start: %s, End: %s, BaseTime: %s, Text: %s' %
                       (start_clip, end_clip, base_time, caption.text))
            click.echo(
                f'StartClip: {step_captions[0].start}, EndClip: {step_captions[-1].end}')
            write_file(output + f'clip{num}.vtt', step_captions, start_clip)
            clips.append({
                'vtt': f'clip{num}.vtt',
                'video': clip_num('clip', num) + '.mp4'
            })
            step_captions = []
            step_seconds = 0
            start_clip = end_clip

    if step_seconds > 0:
        base_time = end_clip
        end_clip = caption.end
        num += 1
        # 在创建视频剪辑时，考虑到视频和字幕可能存在的时间差
        start_time = convert_to_seconds(start_clip)
        end_time = convert_to_seconds(end_clip)
        input_video.subclip(start_time, end_time).write_videofile(
            output + clip_num('clip', num) + '.mp4',
            fps=frames,
        )
        step_captions.append(caption)
        click.echo('Start: %s, End: %s, BaseTime: %s, Text: %s' %
                   (start_clip, end_clip, base_time, caption.text))
        click.echo(
            f'StartClip: {step_captions[0].start}, EndClip: {step_captions[-1].end}')
        write_file(output + f'clip{num}.vtt', step_captions, start_clip)
        clips.append({
            'vtt': f'clip{num}.vtt',
            'video': clip_num('clip', num) + '.mp4'
        })
    with open(output + 'clips.json', 'wt+') as f:
        f.write(json.dumps(clips, indent=True))


if __name__ == '__main__':
    cli()
