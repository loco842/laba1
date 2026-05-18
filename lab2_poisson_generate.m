function events = lab2_poisson_generate()
%LAB2_POISSON_GENERATE Генерация одной реализации потока Пуассона (Вариант 3)
%   lambda(t) = exp(-5t), Omega = [0, 1]
%
%   Используется параметрический метод моделирования на основе
%   функции распределения момента наступления события (формулы 2.4, 2.5).
%
%   Возвращает вектор-строку моментов наступления событий,
%   упорядоченных по возрастанию.

    T  = 1;
    events = [];
    t_prev = 0;

    while true
        % Интеграл интенсивности от t_prev до T (формула 2.4)
        % integral_{t_prev}^{T} exp(-5x) dx = (exp(-5*t_prev) - exp(-5*T)) / 5
        int_lambda = (exp(-5 * t_prev) - exp(-5 * T)) / 5;

        % Вероятность наступления следующего события
        d = 1 - exp(-int_lambda);

        z = rand();

        if z >= d
            break;  % больше событий нет
        end

        % Нахождение момента наступления события методом обратных функций
        % Из уравнения z = 1 - exp(-(exp(-5*t_prev) - exp(-5*t_new))/5):
        %   exp(-5*t_new) = exp(-5*t_prev) + 5*ln(1 - z)
        %   t_new = -ln(exp(-5*t_prev) + 5*ln(1 - z)) / 5
        arg = exp(-5 * t_prev) + 5 * log(1 - z);

        if arg <= 0
            break;
        end

        t_new = -log(arg) / 5;

        if t_new > T || t_new <= t_prev
            break;
        end

        events(end+1) = t_new; %#ok<AGROW>
        t_prev = t_new;
    end
end
