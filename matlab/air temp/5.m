%% 2024 vs 2021 AIR TEMPERATURE ANALYSIS — MATLAB VERSION 
clc; clear; close all;

file_path = "данныепроекта.xlsx";

opts = detectImportOptions(file_path, 'VariableNamingRule','preserve');
T = readtable(file_path, opts);

T.Properties.VariableNames = { ...
    'region','station_id','station_name','date','t_mean','t_max','t_min'};

allEmpty = all(ismissing(T), 2);
T(allEmpty,:) = [];

T.date = datetime(T.date,'InputFormat','dd.MM.yyyy','Format','dd.MM.yyyy');

numVars = ["t_mean","t_max","t_min"];
for v = numVars
    T.(v) = str2double(string(T.(v)));
end

T.year  = year(T.date);
T.month = month(T.date);

T = T(ismember(T.month,[2 3 4]), :);

T.region = string(T.region);


%% TEMPERATURE DIFFERENCE: 2024 – 2021

T24 = T(T.year==2024,:);
T21 = T(T.year==2021,:);

reg24 = groupsummary(T24, ["region","date"], "mean", "t_mean");
reg21 = groupsummary(T21, ["region","date"], "mean", "t_mean");

min_len = min(height(reg24), height(reg21));
reg24 = reg24(1:min_len,:);
reg21 = reg21(1:min_len,:);

reg_diff = table();
reg_diff.region = reg24.region;
reg_diff.date   = reg24.date;
reg_diff.t_diff = reg24.mean_t_mean - reg21.mean_t_mean;

% Plot ΔT
figure('Position',[100 100 1200 700]); hold on;
regions = unique(reg_diff.region);

for r = regions'
    mask = reg_diff.region == r;
    plot(reg_diff.date(mask), reg_diff.t_diff(mask), 'LineWidth',1.6, ...
        'DisplayName', r);
end

yline(0,'--k','HandleVisibility','off');
xlabel("Date");
ylabel("\Delta Temperature (°C)");
% title("Difference in Mean Temperature (2024 - 2021)");
legend show; grid on; xtickangle(45);
print('raznica2024vs2021','-dpng','-r300');


%% dT/dt 
% --- 2024 ---
T24s = sortrows(T24, ["station_id","date"]);
G24 = findgroups(T24s.station_id);
d24_cell = splitapply(@(x){[NaN; diff(x)]}, T24s.t_mean, G24);
T24s.dT = vertcat(d24_cell{:});

% --- 2021 ---
T21s = sortrows(T21, ["station_id","date"]);
G21 = findgroups(T21s.station_id);
d21_cell = splitapply(@(x){[NaN; diff(x)]}, T21s.t_mean, G21);
T21s.dT = vertcat(d21_cell{:});

% Average dT/dt by date
dT24 = groupsummary(T24s, "date", "mean", "dT");
dT21 = groupsummary(T21s, "date", "mean", "dT");

figure('Position',[100 100 1200 700]); hold on;
plot(dT24.date, dT24.mean_dT, 'r','LineWidth',1.6,'DisplayName',"2024");
plot(dT21.date, dT21.mean_dT, 'b','LineWidth',1.6,'DisplayName',"2021");
yline(0,'--k','HandleVisibility','off');
xlabel("Date");
ylabel("dT/dt (°C/day)");
% title("Heating Rate (dT/dt): 2024 vs 2021");
legend show; grid on; xtickangle(45);
print('scorostprogreva2024vs2021','-dpng','-r300');


%% FIRST THAW DATE 

% Thaw function (first t_mean > 0)
find_thaw = @(dates, temps) firstThawFunc(dates, temps);

function out = firstThawFunc(dates, temps)
    mask = temps > 0;
    if any(mask)
        out = dates(find(mask,1,'first'));
    else
        out = NaT;
    end
end

[G, year_g, region_g, station_g] = findgroups(T.year, T.region, T.station_id);

first_thaw_vec = splitapply(@(d,t) find_thaw(d,t), ...
    T.date, T.t_mean, G);

thaw = table(year_g, region_g, station_g, first_thaw_vec, ...
    'VariableNames',{'year','region','station_id','first_thaw'});

figure('Position',[100 100 1200 700]); hold on;

for yr = unique(thaw.year)'
    mask = thaw.year == yr;

    reg_cat = categorical(thaw.region(mask));   % X-axis fix

    scatter(reg_cat, thaw.first_thaw(mask), ...
        60, 'filled', 'DisplayName', string(yr));
end

xlabel("Region");
ylabel("First Day Temperature > 0°C");
% title("First Thaw Date by Station");
legend show; grid on; xtickangle(45);
print('nachalotayania2024vs2021','-dpng','-r300');


%% HEATMAP

monthly = groupsummary(T, ["year","region","month"], "mean", "t_mean");

regions = unique(monthly.region);
years = unique(monthly.year);
months = unique(monthly.month);

colNames = strings(1, numel(years)*numel(months));
heat = NaN(numel(regions), numel(colNames));

idx = 1;
for y = years'
    for m = months'
        colNames(idx) = sprintf("%d_%02d", y, m);
        for r = 1:numel(regions)
            mask = monthly.year==y & monthly.month==m & monthly.region==regions(r);
            row = monthly(mask,:);
            if ~isempty(row)
                heat(r,idx) = row.mean_t_mean;
            end
        end
        idx = idx + 1;
    end
end

figure('Position',[100 100 1200 800]);
imagesc(heat);
colormap('turbo');

cb = colorbar;
cb.Label.String = 'Mean Temperature (°C)';
cb.Label.FontSize = 12;
cb.Label.FontWeight = 'bold';

minT = min(heat(:), [], 'omitnan');
maxT = max(heat(:), [], 'omitnan');
midT = (minT + maxT) / 2;

cb.Ticks = [minT midT maxT];
cb.TickLabels = {
    sprintf('%.1f°C (min)', minT)
    sprintf('%.1f°C (mid)', midT)
    sprintf('%.1f°C (max)', maxT)
};

caxis([minT maxT]);

ylabel("Region");
xlabel("Year–Month");

set(gca, 'YTick', 1:numel(regions), 'YTickLabel', regions);
set(gca, 'XTick', 1:numel(colNames), 'XTickLabel', colNames);
xtickangle(90);

% title("Heatmap: Mean Temperature by Region and Month");
print('heatmap2024vs2021','-dpng','-r300');
