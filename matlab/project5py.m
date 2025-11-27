%   2024 vs 2021 AIR TEMPERATURE ANALYSIS — MATLAB VERSION
%   разница температур, dT/dt, первые даты таяния, heatmap

clc; clear; close all;

file_path = "данныепроекта.xlsx";

opts = detectImportOptions(file_path, 'VariableNamingRule','preserve');
T = readtable(file_path, opts);

T.Properties.VariableNames = { ...
    'region','station_id','station_name','date','t_mean','t_max','t_min'};

T = rmmissing(T);

T.date = datetime(T.date, 'InputFormat','dd.MM.yyyy','Format','dd.MM.yyyy');

T.t_mean = double(T.t_mean);
T.t_max  = double(T.t_max);
T.t_min  = double(T.t_min);

T.year  = year(T.date);
T.month = month(T.date);

T = T(ismember(T.month,[2 3 4]), :);

T.region = string(T.region);

T24 = T(T.year == 2024,:);
T21 = T(T.year == 2021,:);

%  РАЗНИЦА ТЕМПЕРАТУР (2024-2021)

reg24 = groupsummary(T24, {'region','date'}, 'mean', 't_mean');
reg21 = groupsummary(T21, {'region','date'}, 'mean', 't_mean');

min_len = min(height(reg24),height(reg21));
reg24 = reg24(1:min_len,:);
reg21 = reg21(1:min_len,:);

reg_diff = table();
reg_diff.region = reg24.region;
reg_diff.date   = reg24.date;
reg_diff.t_diff = reg24.mean_t_mean - reg21.mean_t_mean;

figure('Position',[100 100 1200 700]);
hold on;

regions = unique(reg_diff.region);
for i = 1:numel(regions)
    mask = reg_diff.region == regions(i);
    plot(reg_diff.date(mask), reg_diff.t_diff(mask), 'DisplayName', regions(i), 'LineWidth', 1.5);
end

yline(0,'--k','LineWidth',1,'HandleVisibility','off');
title("Разница средней температуры (2024 – 2021)", 'FontSize',16,'FontWeight','bold');
xlabel("Дата"); ylabel("ΔT, °C");
legend show; grid on; xtickangle(45);

print('raznica2024vs2021','-dpng','-r300');

%  СКОРОСТЬ ПРОГРЕВА (dT/dt)

T24s = sortrows(T24, {'station_id','date'});
T21s = sortrows(T21, {'station_id','date'});

% dT/dt
T24s.dT = [NaN; diff(T24s.t_mean)];
T21s.dT = [NaN; diff(T21s.t_mean)];

% группировка среднего dT/dt по датам
dT24 = groupsummary(T24s, 'date', 'mean', 'dT');
dT21 = groupsummary(T21s, 'date', 'mean', 'dT');

figure('Position',[100 100 1200 700]);
hold on;

plot(dT24.date, dT24.mean_dT, 'r', 'LineWidth', 1.6, 'DisplayName','2024');
plot(dT21.date, dT21.mean_dT, 'b', 'LineWidth', 1.6, 'DisplayName','2021');

yline(0,'--k','LineWidth',1,'HandleVisibility','off');
title("Скорость прогрева воздуха (dT/dt): 2024 vs 2021", 'FontSize',16,'FontWeight','bold');
xlabel("Дата"); ylabel("dT/dt (°C/день)");
legend show; grid on; xtickangle(45);

print('scorostprogreva2024vs2021','-dpng','-r300');

%   ПЕРВАЯ ДАТА ТАЯНИЯ

% вспомогательная функция
find_thaw = @(date,tmean) conditional_thaw(date, tmean);

function out = conditional_thaw(date, tmean)
    idx = find(tmean > 0, 1, 'first');
    if isempty(idx)
        out = NaT;
    else
        out = date(idx);
    end
end

% группировка по: регион, станция, год
[G, region_g, station_g, year_g] = findgroups(T.region, T.station_id, T.year);

% первая дата таяния в каждой группе
first_thaw_vector = splitapply(@(d,t) conditional_thaw(d,t), T.date, T.t_mean, G);

thaw = table(year_g, region_g, station_g, first_thaw_vector, ...
    'VariableNames', {'year','region','station_id','first_thaw'});

thaw.region = categorical(thaw.region);


figure('Position',[100 100 1200 700]);
hold on;

years = unique(thaw.year);

for i = 1:numel(years)
    mask = thaw.year == years(i);
    scatter(thaw.region(mask), thaw.first_thaw(mask), ...
        70, 'filled', 'DisplayName', string(years(i)));
end

title("Первая дата перехода температуры > 0°C по станциям", 'FontSize',16,'FontWeight','bold');
xlabel("Регион");
ylabel("Дата");
legend show; grid on; xtickangle(45);

print('nachalotayania2024vs2021','-dpng','-r300');

%   HEATMAP

monthly = groupsummary(T, {'region','year','month'}, 'mean', 't_mean');

regions = unique(monthly.region);
years = unique(monthly.year);
months = unique(monthly.month);

% создаём матрицу
heat = NaN(numel(regions), numel(years)*numel(months));

colNames = strings(1, numel(years)*numel(months));
idx = 1;

for y = 1:numel(years)
    for m = 1:numel(months)
        colNames(idx) = sprintf("%d_%02d", years(y), months(m));
        for r = 1:numel(regions)
            row = monthly(monthly.region==regions(r) & monthly.year==years(y) & monthly.month==months(m), :);
            if ~isempty(row)
                heat(r, idx) = row.mean_t_mean;
            end
        end
        idx = idx + 1;
    end
end

figure('Position',[100 100 1200 800]);
imagesc(heat);
colormap('turbo');

cb = colorbar;
cb.Label.String = 'Средняя температура, °C';
cb.Label.FontSize = 12;
cb.Label.FontWeight = 'bold';

title("Heatmap: средняя температура по месяцам, регионам и годам", 'FontSize',16,'FontWeight','bold');
ylabel("Регион");
xlabel("Год_Месяц");

set(gca,'YTick',1:numel(regions),'YTickLabel',regions);
set(gca,'XTick',1:numel(colNames),'XTickLabel',colNames);
xtickangle(90);

print('heatmap2024vs2021','-dpng','-r300');

