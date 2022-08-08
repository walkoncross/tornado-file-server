# -*- coding: utf-8 -*-
"""
check file types

author: zhaoyafei0210@gmail.com
github: https://github.com/walkoncross/tornado-file-server
"""
import os.path as osp


image_extensions = [
    '.jpg',
    '.jpeg',
    '.png',
    '.bmp',
    '.webp',
    '.gif',
    '.tiff'
]

video_extensions = [
    '.mp4',
    '.webm',
    '.ogg',
]

audio_extensions = [
    '.mp3',
    '.wav',
    '.ogg',
]


def is_an_image(file_path):
    """is_an_image

    Args:
        file_path (str): file path

    Returns:
        bool: is an image or not
    """
    _, ext = osp.splitext(file_path)
    # print('--> ext: ', ext)
    return (ext.lower() in image_extensions)


def is_supported_video(file_path):
    """is_supported_video

    Args:
        file_path (str): file path

    Returns:
        bool: is an supported video or not
    """
    _, ext = osp.splitext(file_path)
    # print('--> ext: ', ext)
    return (ext.lower() in video_extensions)


def is_supported_audio(file_path):
    """is_supported_audio

    Args:
        file_path (str): file path

    Returns:
        bool: is an supported audio or not
    """
    _, ext = osp.splitext(file_path)
    # print('--> ext: ', ext)
    return (ext.lower() in audio_extensions)


if __name__=="__main__":
    some_none_supported_extensions = [
        '.avi',
        '.doc',
        '.docx',
        '.pdf',
        '.html',
        '.css'
    ]

    file_extensions = image_extensions + audio_extensions + video_extensions + some_none_supported_extensions

    for ext in file_extensions:
        file_path = 'some_name' + ext
        print("="*32)
        print('--> Is {} an image?'.format(file_path))
        print('--> ', is_an_image(file_path))