%% Лабораторная работа №2: Моделирование потока Пуассона (Вариант 3)
%  lambda(t) = exp(-5t), Omega = [0, 1]

clear; clc; close all;

%% Параметры
T0 = 0;
T  = 1;
N  = 50000;   % Количество реализаций
m  = 50;      % Количество подинтервалов
dt = (T - T0) / m;

% Интенсивность
lambda = @(t) exp(-5*t);

% Среднее число событий на Omega (формула 2.2)
Lambda = (1 - exp(-5*T)) / 5;

% Теоретическая корреляционная функция (формула 2.3)
f2 = @(t1, t2) lambda(t1) .* lambda(t2);

%% Генерация реализаций и сбор статистики
bin_edges   = linspace(T0, T, m + 1);
bin_centers = (bin_edges(1:end-1) + bin_edges(2:end)) / 2;

total_counts = zeros(1, m);
corr_sum     = zeros(m, m);
event_counts = zeros(1, N);

for n = 1:N
    events = lab2_poisson_generate();
    event_counts(n) = length(events);

    % Подсчёт событий в каждом бине
    bc = histcounts(events, bin_edges);
    total_counts = total_counts + bc;

    % Оценка корреляционной функции (формула 1.7)
    corr_sum = corr_sum + (bc' * bc - diag(bc)) / dt^2;
end

% Оценка интенсивности (формула 1.6)
intensity_est = total_counts / (N * dt);

% Оценка корреляционной функции (среднее по N реализациям)
corr_est = corr_sum / N;

%% Точка максимума интенсивности
[~, max_idx] = max(intensity_est);
t_star = bin_centers(max_idx);

%% График 1: Интенсивность
figure('Name', 'Intensity');
t_fine = linspace(T0, T, 500);
plot(t_fine, lambda(t_fine), 'b-', 'LineWidth', 2); hold on;
plot(bin_centers, intensity_est, 'r--o', 'LineWidth', 1.5, 'MarkerSize', 3);
xlabel('t'); ylabel('\lambda(t)');
title('Интенсивность потока Пуассона (Вариант 3)');
legend('Теоретическая \lambda(t) = e^{-5t}', 'Оценка', 'Location', 'best');
grid on;

%% График 2: Сечение корреляционной функции
figure('Name', 'Correlation');
corr_section_theory = f2(t_star, bin_centers);
corr_section_est    = corr_est(max_idx, :);
plot(bin_centers, corr_section_theory, 'b-', 'LineWidth', 2); hold on;
plot(bin_centers, corr_section_est, 'r--o', 'LineWidth', 1.5, 'MarkerSize', 3);
xlabel('t'); ylabel('f_2(t^*, t)');
title(sprintf('Сечение корреляционной функции при t^* = %.4f', t_star));
legend('Теоретическая', 'Оценка', 'Location', 'best');
grid on;

%% График 3: Распределение числа событий
figure('Name', 'Distribution');
max_events = max(event_counts);
k_vals = 0:max_events;

% Теоретическое распределение Пуассона (формула 2.1)
P_theory = exp(-Lambda) * Lambda.^k_vals ./ factorial(k_vals);

% Оценка распределения (формула 1.9)
P_est = zeros(size(k_vals));
for kk = k_vals
    P_est(kk + 1) = sum(event_counts == kk) / N;
end

bar(k_vals - 0.15, P_theory, 0.3, 'FaceColor', [0.2 0.4 0.8]); hold on;
bar(k_vals + 0.15, P_est, 0.3, 'FaceColor', [0.8 0.2 0.2]);
xlabel('k (число событий)'); ylabel('P(k)');
title('Распределение числа событий на \Omega');
legend('Теоретическое (Пуассон)', 'Оценка', 'Location', 'best');
grid on;

%% Критерий хи-квадрат
fprintf('\n=== Критерий хи-квадрат (Лаб. работа 2) ===\n');

observed = zeros(size(k_vals));
for kk = k_vals
    observed(kk + 1) = sum(event_counts == kk);
end
expected = N * P_theory;

% Объединение бинов с ожидаемой частотой < 5
obs_merged = observed;
exp_merged = expected;
while length(exp_merged) > 1 && exp_merged(end) < 5
    obs_merged(end-1) = obs_merged(end-1) + obs_merged(end);
    exp_merged(end-1) = exp_merged(end-1) + exp_merged(end);
    obs_merged(end) = [];
    exp_merged(end) = [];
end
while length(exp_merged) > 1 && exp_merged(1) < 5
    obs_merged(2) = obs_merged(1) + obs_merged(2);
    exp_merged(2) = exp_merged(1) + exp_merged(2);
    obs_merged(1) = [];
    exp_merged(1) = [];
end

chi2_stat    = sum((obs_merged - exp_merged).^2 ./ exp_merged);
df           = length(obs_merged) - 1;
p_value      = 1 - gammainc(chi2_stat/2, df/2);

% Критическое значение хи-квадрат (бисекция по gammainc)
lo = 0; hi = 200;
for iter = 1:200
    mid = (lo + hi) / 2;
    if gammainc(mid/2, df/2) < 0.95
        lo = mid;
    else
        hi = mid;
    end
end
chi2_critical = mid;

fprintf('Статистика хи-квадрат : %.4f\n', chi2_stat);
fprintf('Степени свободы       : %d\n', df);
fprintf('Критическое значение  : %.4f  (alpha = 0.05)\n', chi2_critical);
fprintf('P-значение            : %.4f\n', p_value);
if chi2_stat < chi2_critical
    fprintf('Результат: Гипотеза ПРИНЯТА\n');
else
    fprintf('Результат: Гипотеза ОТКЛОНЕНА\n');
end
