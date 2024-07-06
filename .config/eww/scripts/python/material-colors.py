#!/usr/bin/env python3

import sys
import os
import shutil
import argparse

from jinja2 import Template
from material_color_utilities_python import *
from PIL import Image
from utils import COLORS_DIR, TEMPLATES_DIR, CURRENT_JSON, WALLPAPER_PATH


def get_colors(colorscheme):
    return {
        "primary": hexFromArgb(colorscheme.get_primary()),
        "onPrimary": hexFromArgb(colorscheme.get_onPrimary()),
        "primaryContainer": hexFromArgb(colorscheme.get_primaryContainer()),
        "onPrimaryContainer": hexFromArgb(colorscheme.get_onPrimaryContainer()),
        "secondary": hexFromArgb(colorscheme.get_secondary()),
        "onSecondary": hexFromArgb(colorscheme.get_onSecondary()),
        "secondaryContainer": hexFromArgb(colorscheme.get_secondaryContainer()),
        "onSecondaryContainer": hexFromArgb(colorscheme.get_onSecondaryContainer()),
        "tertiary": hexFromArgb(colorscheme.get_tertiary()),
        "onTertiary": hexFromArgb(colorscheme.get_onTertiary()),
        "tertiaryContainer": hexFromArgb(colorscheme.get_tertiaryContainer()),
        "onTertiaryContainer": hexFromArgb(colorscheme.get_onTertiaryContainer()),
        "error": hexFromArgb(colorscheme.get_error()),
        "onError": hexFromArgb(colorscheme.get_onError()),
        "errorContainer": hexFromArgb(colorscheme.get_errorContainer()),
        "onErrorContainer": hexFromArgb(colorscheme.get_onErrorContainer()),
        "background": hexFromArgb(colorscheme.get_background()),
        "onBackground": hexFromArgb(colorscheme.get_onBackground()),
        "surface": hexFromArgb(colorscheme.get_surface()),
        "onSurface": hexFromArgb(colorscheme.get_onSurface()),
        "surfaceVariant": hexFromArgb(colorscheme.get_surfaceVariant()),
        "onSurfaceVariant": hexFromArgb(colorscheme.get_onSurfaceVariant()),
        "outline": hexFromArgb(colorscheme.get_outline()),
        "shadow": hexFromArgb(colorscheme.get_shadow()),
        "inverseSurface": hexFromArgb(colorscheme.get_inverseSurface()),
        "inverseOnSurface": hexFromArgb(colorscheme.get_inverseOnSurface()),
        "inversePrimary": hexFromArgb(colorscheme.get_inversePrimary())
    }


def get_colors_from_img(image, scheme):
    img = Image.open(image)
    basewidth = 64
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize),Image.Resampling.LANCZOS)
    theme = themeFromImage(img)
    colorscheme = theme.get('schemes').get(scheme)

    return get_colors(colorscheme)


def get_colors_from_color(color, scheme):
    theme = themeFromSourceColor(argbFromHex(color))
    colorscheme = theme.get('schemes').get(scheme)
    
    return get_colors(colorscheme)


def generate_wallpaper(color):
    img = Image.new('RGB', (1920, 1080), color)
    img.save(WALLPAPER_PATH)


def read_config():
    empty = {
        "scheme": "dark", 
        "type": "image", 
        "base_color": None
    }
    
    try:
        with open(CURRENT_JSON, "r") as config:
            return json.load(config)
    except FileNotFoundError:
        with open(CURRENT_JSON, "w") as config:
            json.dump(empty, config)
        return empty
    
    
def write_config(data):
    output_json = json.dumps(data, indent=2)
    with open(CURRENT_JSON, "w") as config:
        config.write(output_json)


def render_templates(colors_list):
    for template in os.listdir(TEMPLATES_DIR):

        with open(f"{TEMPLATES_DIR}/{template}", "r") as file:
            template_rendered = Template(file.read()).render(colors_list)
            
        with open(f"{COLORS_DIR}/{template}", "w") as output_file:
            
            if 'foot' in template or 'hyprland' in template:
                output_file.write(template_rendered.replace('#', ''))
            else:
                output_file.write(template_rendered)

def setup(img):
    try:
        shutil.copyfile(img, WALLPAPER_PATH)
    except shutil.SameFileError:
        pass
    os.system("eww reload")
    os.system("pkill -SIGUSR1 foot")
    os.system(f"gradience-cli apply -p '{COLORS_DIR}/colors-gradience.json' --gtk both")
    os.system(f"swww img {WALLPAPER_PATH} --transition-fps 75 --transition-type wipe --transition-duration 2")


def main(colors, image, scheme, type, base_color):
    render_templates(colors)

    write_config({
        "scheme": scheme, 
        "type": type, 
        "base_color": base_color
    })
    
    setup(image)


if __name__ == "__main__":
    current = read_config()
    scheme = current['scheme']
    type = current['type']
    base_color = current['base_color']

    parser = argparse.ArgumentParser(description="Generate material colors on fly")

    parser.add_argument("--image", type=str, help="Generate color scheme based on an image file.")
    parser.add_argument("--toggle", action="store_true", help="Toggle between light and dark color schemes.")
    parser.add_argument("--current", action="store_true", help="Print current colors scheme(light/dark)")
    parser.add_argument("--type", action="store_true", help="Print current colors type(image/color)")
    parser.add_argument("--color", type=str, help="Generate color scheme based on a color and simple plain wallpaper")

    args = parser.parse_args()

    if args.image:
        colors = get_colors_from_img(args.image, scheme)
        main(colors, args.image, scheme, "image", None)

    elif args.toggle:
        match scheme:
            case "dark":
                scheme = "light"
            case "light":
                scheme = "dark"
            case _:
                scheme = "dark"

        match type:
            case "image":
                colors = get_colors_from_img(WALLPAPER_PATH, scheme)
                main(colors, WALLPAPER_PATH, scheme, "image", None)
                os.system("eww update current_theme=image")

            case "color":
                colors = get_colors_from_color(base_color, scheme)
                generate_wallpaper(colors['surfaceVariant'])
                main(colors, WALLPAPER_PATH, scheme, "color", base_color)
                os.system("eww update current_theme=color")

    elif args.current:
        sys.stdout.write(scheme + "\n")
        sys.stdout.flush()
        
    elif args.type:
        sys.stdout.write(type + "\n")
        sys.stdout.flush()

    elif args.color:
        colors = get_colors_from_color(args.color, scheme)
        generate_wallpaper(colors['secondaryContainer'])
        main(colors, WALLPAPER_PATH, scheme, "color", args.color)
        os.system("eww update current_theme=color")

    else:
        print("No valid argument specified. Use --help for usage information.")
