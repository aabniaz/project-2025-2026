%% SOIL TEMPERATURE COMPARISON — MATLAB VERSION

clc; clear; close all;

file_path = "почва.xlsx";

opts = detectImportOptions(file_path, 'VariableNamingRule','preserve');
opts.DataRange = '2:100000';       
T = readtable(file_path, opts);

T.Properties.VariableNames(1:7) = { ...
    'region','station_id','station_name','date','t_mean','t_max','t_min'};

allEmpty = all(ismissing(T), 2);
T(allEmpty, :) = [];

T.date = datetime(T.date, 'InputFormat','dd.MM.yyyy', 'Format','dd.MM.yyyy');

numVars = {'t_mean','t_max','t_min'};
for i = 1:numel(numVars)
    v = T.(numVars{i});
    T.(numVars{i}) = str2double(string(v));  
end

T.year = year(T.date);
T.month = month(T.date);

T = T(ismember(T.month, [2 3 4]), :);


function d = find_first_thaw_py(date_col, t_col)
    mask = t_col > 0;
    if ~any(mask)
        d = NaT;
    else
        d = date_col(find(mask,1,'first'));
    end
end


years = unique(T.year);
results = struct;

for y = years'
    
    yearT = T(T.year == y, :);

    yearT = sortrows(yearT, {'station_id','date'});

    %% dT_dt 
    yearT.dT_dt = NaN(height(yearT),1);
    G = findgroups(yearT.station_id);

    for g = 1:max(G)
        rows = find(G == g);
        vals = yearT.t_mean(rows);
        yearT.dT_dt(rows) = [NaN; diff(vals)];  
    end

    %% first_thaw 
    [G2, reg2, st2] = findgroups(yearT.region, yearT.station_id);
    thaw = splitapply(@(d,t) find_first_thaw_py(d,t), yearT.date, yearT.t_mean, G2);

    first_thaw = table(reg2, st2, thaw, ...
        'VariableNames', {'region','station_id','first_thaw_date'});

    %% top jumps
    max_jump = splitapply(@(x) max(x, [], 'omitnan'), yearT.dT_dt, G);
    st_unique = splitapply(@(x) x(1), yearT.station_id, G);

    [sortedJ, idx] = sort(max_jump, 'descend');
    top10 = table(st_unique(idx(1:10)), sortedJ(1:10), ...
        'VariableNames', {'station_id','max_dT_dt'});

    %% monthly mean temperatures 
    [G3, reg3, mon3] = findgroups(yearT.region, yearT.month);
    m_mean = splitapply(@(x) mean(x, 'omitnan'), yearT.t_mean, G3);

    monthly_mean = table(reg3, mon3, m_mean, ...
        'VariableNames', {'region','month','t_mean_mean'});

    key = sprintf("Y%d", y);
    results.(key).data = yearT;
    results.(key).first_thaw = first_thaw;
    results.(key).top_jumps = top10;
    results.(key).monthly_mean = monthly_mean;
end


for y = years'
    key = sprintf("Y%d", y);
    fprintf("\n=== ГОД %d ===\n", y);
    disp("Первые даты таяния:");
    disp(results.(key).first_thaw);

    disp("ТОП скачков:");
    disp(results.(key).top_jumps);

    disp("Средняя температура:");
    disp(results.(key).monthly_mean);
end


figure('Position',[100 100 1400 450*numel(years)]);

for i = 1:numel(years)
    y = years(i);
    key = sprintf("Y%d", y);
    data = results.(key).data;

    [G4, reg4, date4] = findgroups(data.region, data.date);
    mean_temp = splitapply(@(x) mean(x, 'omitnan'), data.t_mean, G4);

    reg_daily = table(reg4, date4, mean_temp, ...
        'VariableNames', {'region','date','t_mean'});

    subplot(numel(years), 1, i);
    hold on;

    for r = unique(reg_daily.region)'
        mask = strcmp(reg_daily.region, r{1});
        plot(reg_daily.date(mask), reg_daily.t_mean(mask), ...
             'DisplayName', r{1}, 'LineWidth', 1.4);
    end

    yline(0,'--k','HandleVisibility','off');
    title(sprintf("%d", y), 'FontSize', 16, 'FontWeight','bold');
    xlabel("Date");
    ylabel("Temperature (°C)");
    legend show;
    grid on;
    datetick('x','dd.mm.yyyy','keeplimits');
    xtickangle(45);
end

saveas(gcf, 'soil_temp_2021vs2024.png');
