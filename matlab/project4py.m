% air tempearture comparison of 2021 and 2024 years on MATLAB

clc; clear; close all;

file_path = "данныепроекта.xlsx";

opts = detectImportOptions(file_path, 'VariableNamingRule','preserve');
opts.DataRange = '2:100000';   % аналог header=1
T = readtable(file_path, opts);

disp("Колонки, прочитанные из файла:");
disp(T.Properties.VariableNames);

T.Properties.VariableNames(1:7) = { ...
    'region','station_id','station_name','date','t_mean','t_max','t_min'};

T = rmmissing(T,'MinNumMissing',7);

T.date = datetime(T.date, 'InputFormat','dd.MM.yyyy','Format','dd.MM.yyyy');

T.t_mean = double(T.t_mean);
T.t_max  = double(T.t_max);
T.t_min  = double(T.t_min);

T.year  = year(T.date);
T.month = month(T.date);

% февраль, март, апрель
T = T(ismember(T.month, [2 3 4]), :);

%% первая дата таяния
function d = find_first_thaw(date_col, tmean_col)
    idx = find(tmean_col > 0, 1);
    if isempty(idx)
        d = NaT;
    else
        d = date_col(idx);
    end
end

%%  Анализ по годам
years = unique(T.year);
results = struct;

for y = years'
    yearT = T(T.year == y, :);
    yearT = sortrows(yearT, {'station_id','date'});

    %% dT/dt по станциям
    dT = NaN(height(yearT),1);
    G = findgroups(yearT.station_id);

    for g = 1:max(G)
        rows = find(G == g);
        dT(rows) = [NaN; diff(yearT.t_mean(rows))];
    end

    yearT.dT_dt = dT;

    %% Первая дата оттепели
    [G2, region_id, station_id] = findgroups(yearT.region, yearT.station_id);
    first_thaw_dates = splitapply(@find_first_thaw, yearT.date, yearT.t_mean, G2);

    first_thaw = table(region_id, station_id, first_thaw_dates, ...
        'VariableNames', {'region','station_id','first_thaw_date'});

    %% ТОП-10 скачков
    max_jump = splitapply(@max, yearT.dT_dt, G);
    station_unique = splitapply(@(x) x(1), yearT.station_id, G);

    [sortedJump, idx] = sort(max_jump, 'descend');
    top10 = table(station_unique(idx(1:10)), sortedJump(1:10), ...
        'VariableNames', {'station_id','max_dT_dt'});

    %% Средние температуры по месяцам
    [G3, region3, month3] = findgroups(yearT.region, yearT.month);
    monthly_mean_vals = splitapply(@mean, yearT.t_mean, G3);

    monthly_mean = table(region3, month3, monthly_mean_vals, ...
        'VariableNames', {'region','month','t_mean_mean'});

    key = sprintf("Y%d", y);
    results.(key).data = yearT;
    results.(key).first_thaw = first_thaw;
    results.(key).top_jumps = top10;
    results.(key).monthly_mean = monthly_mean;
end

for y = years'
    key = sprintf("Y%d", y);
    fprintf("\n=============== ГОД %d ===============\n", y);

    disp("Первые даты таяния:");
    disp(results.(key).first_thaw);

    disp("ТОП-10 скачков температуры:");
    disp(results.(key).top_jumps);

    disp("Средняя температура по месяцам:");
    disp(results.(key).monthly_mean);
end

figure('Position',[100 100 1400 350*numel(years)]);

for i = 1:numel(years)
    y = years(i);
    key = sprintf("Y%d", y);
    data = results.(key).data;

    % среднее по регионам
    [G4, region4, date4] = findgroups(data.region, data.date);
    mean_temp = splitapply(@mean, data.t_mean, G4);

    reg_daily = table(region4, date4, mean_temp, ...
        'VariableNames', {'region','date','t_mean'});

    subplot(numel(years), 1, i);
    hold on;

    uregs = unique(reg_daily.region);

    for r = 1:numel(uregs)
        mask = strcmp(reg_daily.region, uregs{r});
        plot(reg_daily.date(mask), reg_daily.t_mean(mask), 'DisplayName', uregs{r}, 'LineWidth', 1.4);
    end

    yline(0,'--k','LineWidth',1,'HandleVisibility','off');
    title(sprintf("Температура воздуха по регионам - %d", y), 'FontSize', 16, 'FontWeight','bold');
    xlabel("Дата");
    ylabel("Температура, °C");
    grid on;
    legend show;

    datetick('x','dd.mm.yyyy','keeplimits');
    xtickangle(45);
end

sgtitle("Air Temperature - Comparison 2021 vs 2024", 'FontSize', 18, 'FontWeight','bold');
