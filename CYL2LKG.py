###############
# CYLview 2 LookingGlass
# For 8x6 quilts for the looking glass portrait.
# Author: Dennis Svatunek
###############

import os
import math
import subprocess

# Set step size of camera to left/right
# 1.3 should give us a roughly 17.5° angle to each side at distance 100
# ALWAYS SET THIS FOR A DISTANCE OF 100! will be calculated to match other camera distances 
# 0 is completely flat, 0.2 is slightly 3D, 0.6 is quite good already
step_size = 1.3
#set distance
camera_distance = 100 # 100 is default, moving further away makes it ever so slightly less 3D. Just leave it at 100
#offset in z direction positive values move the structure behind the plane. proposed values are -0.3 to 0.3
offset_focusplane=0 

#########################
#update step size based on distance
step_size = step_size*camera_distance/100


#CREATE POV INPUT FILES
#########################

# Iterate over POV-Ray files
for file_name in os.listdir('.'):
    if file_name.endswith('.pov') and file_name.startswith('frame_'):
        # Create a directory for output files
        out_dir = file_name[:-4]
        os.makedirs(out_dir, exist_ok=True)

        # Read original camera angle from POV file
        with open(file_name, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith('  angle '):
                camera_angle = float(line.split()[1])
        
        #calculate scene height
        angle_x_radians = math.radians(camera_angle)
        object_height = 100 * math.tan(angle_x_radians)

        # Iterate over angles
        for i in range(48):
            # Calculate x and y positions for camera
            x_pos = (i - 23) * step_size

            # Calculate new FOV angle
            distance = math.sqrt(x_pos**2 + camera_distance**2)
            new_fov = math.atan(object_height / distance)
            print(math.degrees(new_fov))

            # Modify camera location and angle in POV-Ray file
            with open(file_name, 'r') as f:
                lines = f.readlines()
            for j, line in enumerate(lines):
                if line.startswith('camera {'):
                    if 'location <0.0, 0.0, -100.0>' in lines[j+1]:
                        lines[j+1] = f'    location <{x_pos}, 0.0 ,  {-camera_distance}>\n'
                    if 'look_at' in lines[j+2]:
                        lines[j+2] = f'    look_at <0, 0, {-offset_focusplane}>\n'
                    for k in range(j+1, len(lines)):
                        if 'angle' in lines[k]:
                            lines[k] = f'    angle {math.degrees(new_fov)}\n'
                            break  # break out of loop once angle is updated
            # Write modified POV-Ray file for this frame
            frame_num_str = str(i).zfill(2)
            frame_file_name = f'{out_dir}/{file_name[:-4]}_v{frame_num_str}.pov'
            with open(frame_file_name, 'w') as f:
                f.writelines(lines)

#RENDER
#########################
command = 'find . -maxdepth 1 -type d -name "frame_*" -exec sh -c \'cd "{}" && for i in *.pov; do povray $i +W420 +H560 -d +Q11 +A; done\' \\;'
subprocess.run(command, shell=True)

#MAKE QUILTS
#########################

from PIL import Image

# Define output image dimensions and layout
num_cols = 8
num_rows = 6
img_width = 420
img_height = 560
total_width = num_cols * img_width
total_height = num_rows * img_height

# Iterate over frame directories
for dir_name in os.listdir('.'):
    if dir_name.startswith('frame_') and os.path.isdir(dir_name):
        # Create new image and iterate over individual images
        quilt_img = Image.new('RGB', (total_width, total_height))
        for i in range(48):
            # Calculate image position in output image
            col_idx = i % num_cols
            row_idx = i // num_cols
            x_pos = col_idx * img_width
            y_pos = (num_rows - row_idx - 1) * img_height

            # Open image and paste into output image
            img_name = f'{dir_name}/{dir_name}_v{i:02d}.png'
            img = Image.open(img_name)
            quilt_img.paste(img, (x_pos, y_pos))

        # Save output image
        quilt_name = f'quilt_{dir_name}_qs8x6a0.75.png'
        quilt_img.save(quilt_name)

#MAKE VIDEO IF MORE THAN ONE PNG
#########################
png_files = [f for f in os.listdir() if f.endswith('.png')]
# Only execute ffmpeg command if there is more than one PNG file
if len(png_files) > 1:
    # Execute ffmpeg command
    command = f"ffmpeg -r 30 -f image2 -s 3060x3060 -i quilt_frame_f%03d_qs8x6a0.75.png -vcodec libx265 -crf 20 -pix_fmt yuv420p animation_qs8x6a0.75.mp4"
    os.system(command)
