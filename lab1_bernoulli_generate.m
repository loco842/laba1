function events = lab1_bernoulli_generate()
%LAB1_BERNOULLI_GENERATE Генерация одной реализации потока Бернулли (Вариант 3)
%   k = 3 источника
%   s1(t) = sin(t), s2(t) = -cos(t), s3(t) = -cos(2t)
%   Omega = [pi/2, 3*pi/4]
%
%   Возвращает вектор-строку моментов наступления событий,
%   упорядоченных по возрастанию.

    events = [];

    % Вероятности порождения событий каждым источником
    % p_i = integral of s_i(t) over Omega
    p1 = sqrt(2)/2;       % int_{pi/2}^{3pi/4} sin(t) dt = sqrt(2)/2
    p2 = 1 - sqrt(2)/2;   % int_{pi/2}^{3pi/4} (-cos(t)) dt = 1 - sqrt(2)/2
    p3 = 0.5;             % int_{pi/2}^{3pi/4} (-cos(2t)) dt = 1/2

    % Источник 1: s1(t) = sin(t)
    % Условная плотность: rho1(t) = sin(t) / p1
    % CDF: F1(t) = -sqrt(2)*cos(t)
    % Обратная CDF: F1^{-1}(u) = acos(-u / sqrt(2))
    if rand() < p1
        u = rand();
        events(end+1) = acos(-u / sqrt(2));
    end

    % Источник 2: s2(t) = -cos(t)
    % Условная плотность: rho2(t) = -cos(t) / p2
    % CDF: F2(t) = (1 - sin(t)) / (1 - sqrt(2)/2)
    % Обратная CDF: F2^{-1}(u) = pi - asin(1 - u*(1 - sqrt(2)/2))
    if rand() < p2
        u = rand();
        events(end+1) = pi - asin(1 - u * (1 - sqrt(2)/2));
    end

    % Источник 3: s3(t) = -cos(2t)
    % Условная плотность: rho3(t) = -cos(2t) / p3
    % CDF: F3(t) = -sin(2t)
    % Обратная CDF: F3^{-1}(u) = (pi + asin(u)) / 2
    if rand() < p3
        u = rand();
        events(end+1) = (pi + asin(u)) / 2;
    end

    % Сортировка моментов наступления событий по возрастанию
    events = sort(events);
end
