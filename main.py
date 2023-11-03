import os
import click
import webvtt
import datetime
import time
from moviepy.editor import VideoFileClip


@click.group()
def cli():
    pass


def convert_to_seconds(s):
    x = time.strptime(s.split('.')[0], '%H:%M:%S')
    return datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()


@cli.command()
@click.option('--vtt', prompt='Your vtt file', help='The vtt file of the video')
@click.option('--video', prompt='Your video file', help='The video file to split')
@click.option('--output', prompt='Your output folder', help='The output folder', default='./')
@click.option('--duration', prompt='Your duration(minutes)', help='The duration of the split', default=3, type=int)
def split_video(vtt, video, output='./', duration=3):
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
    start_clip = ''
    end_clip = ''
    step_seconds = 0
    step_captions = []
    num = 0
    for caption in webvtt.read(vtt):
        if step_seconds == 0:
            start_clip = caption.start

        start = convert_to_seconds(caption.start)
        end = convert_to_seconds(caption.end)

        span = end - start
        step_seconds = step_seconds + span

        if step_seconds >= duration:
            end_clip = caption.end
            click.echo('Start: %s, End: %s' % (start_clip, end_clip))
            num += 1
            input_video.subclip(start_clip, end_clip).write_videofile(
                output + f'clip{num}' + '.mp4',
                fps=frames,
                bitrate="4000k",
                threads=1,
                preset='ultrafast',
                codec='h264'
            )
            step_captions = []
            step_seconds = 0

        step_captions.append(caption)

    if step_seconds > 0:
        end_clip = caption.end
        click.echo('Start: %s, End: %s' % (start_clip, end_clip))
        num += 1
        input_video.subclip(start_clip, end_clip).write_videofile(
            output + f'clip{num}' + '.mp4',
            fps=frames,
            bitrate="4000k",
            threads=1,
            preset='ultrafast',
            codec='h264'
        )


if __name__ == '__main__':
    cli()
