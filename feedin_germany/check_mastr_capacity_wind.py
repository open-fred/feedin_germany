import pandas as pd

import feedin as f
import mastr_power_plants as mastr

######################
# 50 Hertz Zeitreihe: zu hohe Werte + zu hohe installierte Leistung
# mögliche Gründe:
# # Offshore noch nicht ausgefiltert --> geringer Anteil, circa 1 GW
# # decommissioning nur 2019, 2050 --> Daten fehlen? Lösung: stilllegung nach x Jahren

year = 2017  # first complete mastr is looked at then the pp for this year (already installed, not decommissioned)

mastr_pp = mastr.helper_load_mastr_from_file(category='Wind',
                                             additional_cols=['Bruttoleistung',
                                                              'Nettonennleistung',
                                                              'GeplantesInbetriebnahmedatum'])

# Mastr onshore and offshore
print('######## complete MaStR typev2 ########')
print(mastr_pp.groupby('Lage').size())

cap_land = mastr_pp.loc[mastr_pp['Lage'] == 'WindAnLand']['InstallierteLeistung'].sum() / 1e6
cap_see = mastr_pp.loc[mastr_pp['Lage'] == 'WindAufSee']['InstallierteLeistung'].sum() / 1e6

print('InstallierteLeistung Land: {} GW, InstallierteLeistung See: {}GW'.format(
    round(cap_land, 2), round(cap_see, 2)))

# InstallierteLeistung vs Bruttoleistung vs Nettoleistung
cap_land_brutto = mastr_pp.loc[mastr_pp['Lage'] == 'WindAnLand']['Bruttoleistung'].sum() / 1e6
cap_land_netto = mastr_pp.loc[mastr_pp['Lage'] == 'WindAnLand']['Nettonennleistung'].sum() / 1e6
cap_see_brutto = mastr_pp.loc[mastr_pp['Lage'] == 'WindAufSee']['Bruttoleistung'].sum() / 1e6
cap_see_netto = mastr_pp.loc[mastr_pp['Lage'] == 'WindAufSee']['Nettonennleistung'].sum() / 1e6

df = pd.DataFrame({'brutto': [cap_land_brutto, cap_see_brutto],
                   'netto': [cap_land_netto, cap_see_netto],
                   'install': [cap_land, cap_see]}, index=['Land', 'See'])

print(df)
print()

# com and decom dates
dates = mastr_pp[['Inbetriebnahmedatum', 'DatumEndgueltigeStilllegung',
                  'GeplantesInbetriebnahmedatum',
                  'DatumBeginnVoruebergehendeStilllegung', 'DatumWiederaufnahmeBetrieb']]
print(dates.groupby('DatumEndgueltigeStilllegung').size())




print()
print()
print('######## MaStR typev2 year {} ########'.format(year))
mastr_pp_year = mastr.get_mastr_pp_filtered_by_year(energy_source='Wind',
                                                    year=year)

cap_land = mastr_pp_year.loc[mastr_pp_year['Lage'] == 'WindAnLand']['capacity'].sum() / 1e6
cap_see = mastr_pp_year.loc[mastr_pp_year['Lage'] == 'WindAufSee']['capacity'].sum() / 1e6

print('capacity Land {}: {} GW, capacity See {}: {}GW'.format(year,
    round(cap_land, 2), round(cap_see, 2), year))

# Lebensdauer == 20 Jahre
mastr_pp_year_20 = mastr.get_mastr_pp_filtered_by_year(energy_source='Wind',
                                                    year=year, decom_20=True)

cap_land_20 = mastr_pp_year_20.loc[mastr_pp_year_20['Lage'] == 'WindAnLand']['capacity'].sum() / 1e6
cap_see_20 = mastr_pp_year_20.loc[mastr_pp_year_20['Lage'] == 'WindAufSee']['capacity'].sum() / 1e6

print('capacity Land {}, decom 20: {} GW, capacity See {}, decom 20: {} GW'.format(
    year, round(cap_land_20, 2), round(cap_see_20, 2), year))

# installed cap 50 hz
cap_50hz = f.get_50hz_capacity(year=year, category='Wind') / 1e6
print('Installed capacity 50 Hertz in {} {} GW'.format(year, cap_50hz))

# diff %:
diff = (cap_land - cap_50hz) / cap_50hz * 100
print(diff)