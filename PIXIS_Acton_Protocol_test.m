%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Version history
%2017-11-21 Jingda
%  - optimizing workflow

%2017-8 Lisa
%  - Initial SP2300i control matlab code

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function PIXIS_Action_Protocol_test()
close all;
clear all;
clc;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Configuration of SP2300i parameters
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
start_wave = 778;% center wavelength in nm
start_grating = 1;% grating 1 = 1800 grooves/mm Blz = 500 nm, grating 2 = 300 grooves/mm Blz = 750 nm

background = 0; %if 1, take a background image and subtract noise
dynamic = 0; % keep capturing images if 1, or 1 image at a time if 0
exposure = 1000; % in ms
gain = 1;
shutter = 3; % 1.) Always Closed 2.) Always Op1en 3.) Normal 4.) Open Before Trigger
shutterdelay = 0;
t_image = 30; %s, how long for dynamic update
n_image = t_image/exposure*1000; 
line_cam = 0; %which line to view, average the whole image if 0

%clear up previously undeleted devices
delete(instrfindall); 

import mmcorej.*;
mmc = CMMCore;
mmc.unloadAllDevices
mmc.loadSystemConfiguration ('MMConfig.cfg');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Beginning of control parameters for SP2300i %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% connects to the serial port and opens access to the device
% information about the next three lines can be found:
% https://www.mathworks.com/help/matlab/ref/serial.html 
s = serial('COM4');
set(s,'BaudRate',9600,'Terminator','CR','Timeout',100);
fopen(s);

% type of grating 
if start_grating == 1
    grating_num = 1800;
else
    grating_num = 300;
end

disp('Changing the grating to:  '), disp(grating_num)
disp('Changing the wavelength to:  '), disp(start_wave)
disp('Please hold on for a moment while these changes are being made. Thanks!')
% goes to the central wavelength at the maximum speed
% returns a statement that indicates whether the command was followed
goto_nm_max_speed(s,start_wave);
% sets the grating of choice
% returns a statement that indicates whether the command was followed
set_grating(s,start_grating);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% End of control parameters for SP2300i %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Beginning of Calibration Function %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% note: so far everything is in terms of mm
% number of pixels from the centre
nth_pixel = linspace(1,670,3);
% Central wavelength
lambda = (start_wave)*1e-6;
% pixel width um
x = 20*1e-3;
% focal length mm
f = 300;
% inclusion angle (degrees)
gamma = 30.3;
% detector angle (degrees)
delta = 1.38; 
% diffraction order
m = 1;
% distance between grooves in mm
d = 1/grating_num;

% predicts the value of lambda at pixel n 
% these equations come from pages 503-505 of the WinSpec Software User
% Manual, version 2.4M
lambda_at_pixel = [];

for i = nth_pixel
    zeta_angle = i*x*cosd(delta)/(f+i*x*sind(delta));
    zeta = (atand(zeta_angle)); 
    psi = asind(m*lambda/(2*d*cosd(gamma/2))); % psi is the rotational angle of the grating
    lambda_prime = ((d/m)*(sind(psi - (gamma/2)) + sind(psi + (gamma/2) + zeta)))*1e-3;
    lambda_at_pixel = [lambda_at_pixel lambda_prime];
end

% use linear regression to fit the data to a second degree polynomial,
% where it solves for the values of the coefficients
pixel_points = [670,1005,1340];
fit = polyfit(pixel_points,lambda_at_pixel,2);
true_lambda = [];
% converts the pixel number to wavelength using the coefficients found
% above
for k = linspace(1,1340,1340)
    lambda = (fit(1)*(k)^2 + fit(2)*k + fit(3))*1e+9;
    true_lambda = [true_lambda lambda];
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% End of Calibration Function %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Beginning of Camera Parameters, Image Acquisition, Subraction of 
%%% Background Noise, and Graphing of Data %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% the above loads the configuration file. HOWEVER, this does not that the
% camera will read all of those values. We have to set the device to those
% specific values

% the following makes sure that the camera operates at the correct
% temperature
pixis_temp = str2double(mmc.getProperty('PIXIS','CCDTemperature'));
disp(pixis_temp);

while pixis_temp > -75
    pixis_temp = str2double(mmc.getProperty('PIXIS','CCDTemperature'));
    disp('Please wait until the camera cools to -75 C. The current temperature is:     '), disp(pixis_temp);
    pause(5)
%     if pixis_temp == -75.0000
%         break 
%     end 
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% This next section asks the user to input parameters for the camera
%%% using propmts. More information about the camera functions can be found
%%% here: https://micro-manager.org/wiki/Micro-Manager_Programming_Guide
%%% and here: https://javadoc.imagej.net/Micro-Manager-Core/mmcorej/CMMCore.html
%%% There is another section within this one that is currently commented
%%% out. It simply prints out the camera settings so that you know you
%%% input them correctly. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

mmc.setProperty('PIXIS','Exposure',exposure);
mmc.setProperty('PIXIS','Gain',gain)

if shutter == 1
    shutter = 'Always Closed';
else
    if shutter == 2
        shutter = 'Always Open';
    else
        if shutter == 3
            shutter = 'Normal';
        else
            shutter = 'Open Before Trigger';
        end
    end
end

mmc.setProperty('PIXIS','ShutterMode',shutter)
mmc.setProperty('PIXIS','ShutterCloseDelay',shutterdelay);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% End of camera parameters
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

if background == 1
    disp('Taking a background image. . .');
    % the code for taking an image came from:
    % https://micro-manager.org/wiki/Matlab_Configuration, and then some slight
    % modifications were made
    mmc.snapImage();        
    img = mmc.getImage();  
    width = mmc.getImageWidth();
    height = mmc.getImageHeight();
    if mmc.getBytesPerPixel == 2    
        pixelType = 'uint16';   
        bits = 16;
    else
        pixelType = 'uint8';  
        bits = 8;
    end   
    img = typecast(img, pixelType);      % converts the data of the image to that of the pixelType
    img = reshape(img, [width, height]); % shaping the image to that of the width and height parameters
    img = transpose(img);                % this gives us back a matrix of 100 x 1340  
    % information about the Tiff library can be found here: http://www.simplesystems.org/libtiff/
    t = Tiff('background_image.tif','w');% these lines save the image so that its data and format are not changed or manipulated
    t.setTag('Photometric',Tiff.Photometric.MinIsBlack);
    t.setTag('BitsPerSample',bits);
    t.setTag('SamplesPerPixel',1);
    t.setTag('SampleFormat',Tiff.SampleFormat.UInt);
    t.setTag('ImageLength',100);
    t.setTag('ImageWidth',1340);
    t.setTag('RowsPerStrip',100);
    t.setTag('PlanarConfiguration',Tiff.PlanarConfiguration.Chunky);
    t.write(img);
    t.close();
else
    img = zeros(100,1340,'uint16');
    t = Tiff('background_image.tif','w'); 
    t.setTag('Photometric',Tiff.Photometric.MinIsBlack);
    t.setTag('BitsPerSample',16);
    t.setTag('SamplesPerPixel',1);
    t.setTag('SampleFormat',Tiff.SampleFormat.UInt);
    t.setTag('ImageLength',100);
    t.setTag('ImageWidth',1340);
    t.setTag('RowsPerStrip',100);
    t.setTag('PlanarConfiguration',Tiff.PlanarConfiguration.Chunky);
    t.write(img);
    t.close();
end
back_img=img; 

prompt = ['Is the lightsource ready and running?' newline newline 'Input 1 for "YES" and 0 for "NO":     '];
answer = input(prompt);
if answer == 1
    disp('Okay!')
else
    disp('Please turn on the light source!');
    pause(5)
    propmt = ['Is the lightsource ready and running?' newline newline 'Input 1 for "YES" and 0 for "NO":     '];
    answer = input(prompt);
    if answer == 1
        disp('Okay!')
    else 
        disp('If you want to quit the program please do so ("CTRL-C") and unload the devices');
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Acquiring and calibrating the images
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

disp('Camera will now take the images and the program will analyze them!')
i = 1;

figure(1)
% plotting the intensity as a function of the calibrated wavelength  
fig = plot(NaN,NaN);
title('corrected spectrum')
% ylim([-10 500]);
xlabel('Wavelength (nm)')
ylabel('Intensity')

while i <= n_image
    mmc.snapImage();    
    img = mmc.getImage();  
    width = mmc.getImageWidth();
    height = mmc.getImageHeight();
    if mmc.getBytesPerPixel == 2
        pixelType = 'uint16';
        bits = 16;
    else
        pixelType = 'uint8';
        bits = 8;
    end

    img = typecast(img, pixelType);      % these three lines are the same idea as the ones above
    img = reshape(img, [width, height]); 
    img = transpose(img);
    %I = imshow(img); % shows the image taken 
%     c = clock;
    % the name of the file is saved according to the present date and time
    % format example: 2017-7-5T13-58-50 -> July 5th, 2017 1:58:50 PM
%     initial_name = strcat(int2str(c(1)),'-',int2str(c(2)),'-',int2str(c(3)),'T',int2str(c(4)),'-',int2str(c(5)),'-',int2str(c(6)));
%     full_name = strcat('Raw_Image_Data_',initial_name,'.tif'); % saves the image according to the date and time it was taken at
%     t = Tiff(full_name,'w');
%     t.setTag('Photometric',Tiff.Photometric.MinIsBlack);
%     t.setTag('BitsPerSample',bits);
%     t.setTag('SamplesPerPixel',1);
%     t.setTag('SampleFormat',Tiff.SampleFormat.UInt);
%     t.setTag('ImageLength',100);
%     t.setTag('ImageWidth',1340);
%     t.setTag('RowsPerStrip',100);
%     t.setTag('PlanarConfiguration',Tiff.PlanarConfiguration.Chunky);
%     t.write(img);
%     t.close();
%     % loads the image we just took along with the background image
%     current_image = imread(full_name);
%     background_image = imread('background_image.tif');

%     difference = imsubtract(current_image,background_image); % subtracts the background image from the spectrum 
    difference = imsubtract(img,back_img); % subtracts the background image from the spectrum 
    
    if line_cam == 0
        intensity(i,1:1340) = sum(difference)/100;
    else
        intensity(i,1:1340) = difference(line_cam,:);   % finds the sums of each of the columns and then calculates the average value
    end
        % intensity is an array
    plot(true_lambda,intensity(i,1:1340)); axis tight;
    drawnow;
%     set(fig,'XData',true_lambda,'YData',intensity(i,1:1340));
    
%     pause(0.01);
%     c = clock;
%     plot_name = strcat('spectrum_',initial_name,'.tif'); % saves the image according to the date and time it was taken at
%     saveas(fig,plot_name);

    i = i + 1;
    clear img
end 

figure(2)
plot(true_lambda,intensity);

disp('Program is finished! Have a nice day!');

mmc.unloadAllDevices % unloads the camera and the configuration file
fclose(s);      % the following then makes sure that the spectrometer is unloaded
delete(instrfindall) % all remaining instruments are deleted and the serial port is closed and cleared of any instruments
clear s
9;

end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% End of Image Acquisition, Subraction of Background Noise, and Calibration %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Functions for SP2300i %%%
%%% inspiration for this code came from: http://juluribk.com/2014/09/19/controlling-sp2150i-monochromator-with-pythonpyvisa/
%%% however, we changed the way that our device communicates with the
%%% computer as well as changed to code to run in matlab. As well, some of
%%% the functions were omitted because they were irrelevant to our device
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% the explanations for these functions can be found in the device manual 
function get_nm(s)
fprintf(s,'?NM');
fscanf(s)
end 

function get_nm_per_min(s)
fprintf(s,'?NM/MIN');
fscanf(s)
end

function get_serial_num(s)
fprintf(s,'SERIAL');
fscanf(s)
end 

function get_model_num(s)
fprintf(s,'MODEL');
fscanf(s)
end 

function goto_nm_max_speed(s,nm)
A = nm;
B = sprintf('%0.2f GOTO', A);
fprintf(s,B);
fscanf(s)
end

function get_turret(s)
fprintf(s,'?TURRET');
fscanf(s)
end

function get_filter(s)
fprintf(s,'?FILTER');
fscanf(s)
end

function get_grating(s)
fprintf(s,'?GRATING');
fscanf(s)
end

function set_turret(s,num)
if num <=2
    v0 = int8(num);
    v1 = int2str(v0);
    v2 = ' ';
    v3 = ' TURRET';
    v = strcat(v1,v2,v3);
    fprintf(s,v);
    fscanf(s)
else
    disp('There is no turret with this input')
end
end 

function set_filter(s,num)
if num <= 6
    v0 = int8(num);
    v1 = int2str(v0);
    v2 = ' ';
    v3 = ' FILTER';
    v = strcat(v1,v2,v3);
    fprintf(s,v);
    fscanf(s)
    disp('Filter changed and waiting with additional delay...');
    pause(1)
    disp('Done Waiting');
else
    disp('There is no filter with this input')
end 
end 

function set_grating(s,num)
if num <=2
    v0 = int8(num);
    v1 = int2str(v0);
    v2 = ' ';
    v3 = ' GRATING';
    v = strcat(v1,v2,v3);
    fprintf(s,v);
    fscanf(s)
else
    fprintf('There is no grating with this input')
end
end

function goto_nm_with_set_nm_per_min(s,nm,nm_per_min)
A = nm_per_min; 
B = sprintf('%0.2f NM/MIN', A);
fprintf(s,B);
C = nm;
D = sprintf('%0.2f >NM', C);
fprintf(s,D);
char = 0;
while char ~= 1
    A = fprintf(s,'MONO-?DONE');
    char = int8(A(2));
    pause(.2);
end
if char == 1
    disp('Scan is done!')
else
    disp('Scan is not done')
end 
fprintf(s,'MONO-STOP');
fprintf(s,'?NM');
fscanf(s)
end
function init_wavelength(s, start_wave)
A = sprintf('%0.2f INIT-WAVELENGTH', start_wave);
fprintf(s,A);
fscanf(s)
end 

function init_grating(s, start_grating)
A = sprintf('%0.2f INIT-GRATING', start_grating);
fprintf(s,A);
fscanf(s)
end 

function init_srate(s, start_rate)
A = sprintf('%0.2f INIT-SRATE', start_rate);
fprintf(s,A);
fscanf(s)
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% End of Functions for SP2300i %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%