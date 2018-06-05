nth_pixel = linspace(1,670,3);
% Central wavelength
lambda = 528e-6;


% pixel width um
x = 20*1e-3;
% focal length mm
f = 300;
% inclusion angle (degrees)
gamma = 30.3;
% detector angle (degrees)
delta = 1.38;
% type of grating 
% if start_grating == 1
%     grating_num = 1800;
% else
%     grating_num = 300;
% end 
grating_num = 300;
% diffraction order
m = 1;
% distance between grooves
d = 1/grating_num;

% predicts the value of lambda at pixel n 
% these equations come from pages 503-505 of the WinSpec Software User
% Manual, version 2.4M
lambda_at_pixel = [];
for i = nth_pixel
    zeta_angle = i*x*cosd(delta)/(f+i*x*sind(delta));
    zeta = (atand(zeta_angle));
    % psi is the rotational angle of the grating 
    psi = asind(m*lambda/(2*d*cosd(gamma/2)));
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

