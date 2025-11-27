%% AIR TEMPERATURE COMPARISON — MATLAB VERSION 

clc; clear; close all;

file_path = "данныепроекта.xlsx";

opts = detectImportOptions(file_path, 'VariableNamingRule','preserve');
opts.DataRange = '2:100000';        % Python header=1
T = readtable(file_path, opts);

disp("Колонки, прочитанные из файла:");
disp(T.Properties.VariableNames);

T.Properties.VariableNames(1:7) = { ...
    'region','station_id','station_name','date','t_mean','t_max','t_min'};

allEmpty = all(ismissing(T), 2);
T(allEmpty, :) = [];

T.date = datetime(T.date, 'InputFormat','dd.MM.yyyy', 'Format','dd.MM.yyyy');

numVars = {'t_mean','t_max','t_min'};
for i = 1:numel(numVars)
    col = string(T.(numVars{i}));
    T.(numVars{i}) = str2double(col);  
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

    %% dT/dt
    yearT.dT_dt = NaN(height(yearT),1);
    G = findgroups(yearT.station_id);

    for g = 1:max(G)
        rows = find(G == g);
        vals = yearT.t_mean(rows);
        yearT.dT_dt(rows) = [NaN; diff(vals)];
    end

    %% First thaw
    [G2, reg2, st2] = findgroups(yearT.region, yearT.station_id);
    thaw = splitapply(@(d,t) find_first_thaw_py(d,t), yearT.date, yearT.t_mean, G2);

    first_thaw = table(reg2, st2, thaw, ...
        'VariableNames', {'region','station_id','first_thaw_date'});

    %% Топ-10 скачков 
    max_jump = splitapply(@(x) max(x, [], 'omitnan'), yearT.dT_dt, G);
    st_unique = splitapply(@(x) x(1), yearT.station_id, G);

    [sortedJ, idx] = sort(max_jump, 'descend');
    take = min(10, numel(idx));   % защита
    top10 = table(st_unique(idx(1:take)), sortedJ(1:take), ...
        'VariableNames', {'station_id','max_dT_dt'});

    %% Средние температуры по месяцам 
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

    [G4, reg4, date4] = findgroups(data.region, data.date);
    mean_temp = splitapply(@(x) mean(x, 'omitnan'), data.t_mean, G4);

    reg_daily = table(reg4, date4, mean_temp, ...
        'VariableNames', {'region','date','t_mean'});

    subplot(numel(years), 1, i);
    hold on;

    uregs = unique(reg_daily.region);

    for r = 1:numel(uregs)
        mask = strcmp(reg_daily.region, uregs{r});
        plot(reg_daily.date(mask), reg_daily.t_mean(mask), ...
             'DisplayName', uregs{r}, 'LineWidth', 1.4);
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


saveas(gcf, 'air_temp_2021vs2024.png');
