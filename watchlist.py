# -*- coding: utf-8 -*-
"""
Team Watchlist for Signal Prioritization
Two categories:
1. Elite defensive teams (when playing equals, not mismatches)
2. Low-tier teams with strong Under 2.5 track record
"""

# ===========================================
# ELITE DEFENSIVE TEAMS
# ===========================================
# Priority when playing against BALANCED opponents (not crushing weaker teams)
ELITE_DEFENSIVE_TEAMS = {
    # Russian Premier League
    "Динам

о Махачкала", "Балтика", "Рубин", "Зенит",
    
    # Portuguese Primeira Liga
    "Porto", "FC Porto",
    
    # Romanian Liga 1
    "FCSB", "FCSB Bucuresti", "CFR Cluj",
    
    # Hungarian NB I
    "Paks", "Ferencvaros", "Ferencvárosi TC",
    
    # Spanish La Liga
    "Atletico Madrid", "Atlético Madrid", "Real Sociedad",
    
    # Italian Serie A
    "Inter", "Inter Milan", "Napoli", "Juventus", "Roma", "Milan", "AC Milan",
    
    # French Ligue 1
    "Lille", "Lens", "Monaco", "AS Monaco",
    
    # English Premier League
    "Everton",
    
    # German Bundesliga
    "Eintracht Frankfurt", "Stuttgart", "VfB Stuttgart", "Bayer Leverkusen",
    
    # Belgian Pro League
    "Anderlecht", "Genk", "KRC Genk",
    
    # Dutch Eredivisie
    "PSV", "PSV Eindhoven", "Ajax", "AFC Ajax"
}

# ===========================================
# LOW-TIER HIGH-PERCENTAGE TEAMS
# ===========================================
# Teams with 85%+ Under 2.5 record (100 teams from user list)
LOW_TIER_STARS = {
    # 100% U2.5 (17 teams)
    "RC Bobo-Dioulasso", "Aueta", "Dynamo Abomey", "Singida Black Stars", 
    "Dong Thap",
    
    # 95% U2.5 (2 teams)
    "Samartex", "Fard Alborz",
    
    # 94% U2.5 (8 teams)
    "Fasil Ketema", "Siwelele", "Mufulira Wanderers", "Green Eagles",
    "NAPSA Stars", "Nchanga Rangers", "Kansanshi Dynamos",
    
    # 93% U2.5 (2 teams)
    "Atletico ECCA", "Pharco",
    
    # 92% U2.5 (9 teams)
    "Fundadores", "Pikine", "Jaraaf", "Teungueth", "AJEL",
    "Derby Academie", "Union Sportive Boujaad", "Academica do Lobito", "Kabuscorp",
    
    # 91% U2.5 (3 teams)
    "Namungo", "Gubbio", "Aversa Normanna",
    
    # 90% U2.5 (6 teams)
    "La Solana", "UD Melilla II", "Tanzania Prisons", "Shahrdari Noshahr",
    "Ario Eslamshahr",
    
    # 89% U2.5 (4 teams)
    "Kedus Giorgis", "Stade Malien Bamako", "Raja Casablanca", "Shams Azar Qazvin",
    
    # 88% U2.5 (5 teams)
    "Sekhukhune United", "Zacatepec", "Sporting Cascades", "Karystos", "Nkana",
    
    # 87% U2.5 (30 teams)
    "Konkola Blades", "Kabwe Warriors", "Zanaco", "Sesvete", "AS Cotonou",
    "Mathare United", "Al Qadisiyah Bani Walid", "Dikhil", "Azam",
    "Entebbe UPPC", "Al Quwa Al Jawiya", "General Paz Juniors", "Salgueiros",
    "Kaizer Chiefs", "Vilaverdense", "Katsina United", "Abia Warriors",
    "St Maur Lusitanos",
    
    # 86% U2.5 (21 teams)
    "Tanta SC", "Dayrout", "Bandari", "XV de Piracicaba", "Votuporanguense",
    "Inter de Limeira", "Al Watan", "Estudiantes de San Luis", "Merreikh Kosti",
    "Hilal El-Fasher", "Al Fallah", "Porto Vitoria", "Eastern District",
    "Police XI", "UD Ourense", "Porreres", "FC Siena", "Pompei",
    "Virtus Ciserano Bergamo", "Smouha SC", "El Gounah",
    
    # 85% U2.5 (19 teams)
    "Cuarte", "Villacanas", "Durango", "Hearts of Oak", "Arenas Armilla",
    "Mes Kerman", "Lamboi", "Gor Mahia", "Yuksekova Belediyespor W",
    "US Ouakam", "Stade de Mbour", "Wally Daan", "Mashujaa", "1° de Maio",
    "CD Lunda-Sul", "Chabab Atlas Khenifra", "Thap Luang United", "Safa",
    
    # 84% U2.5 (1 team)
    "Kai out Couth"
}

# Combined watchlist
ALL_WATCHLIST_TEAMS = ELITE_DEFENSIVE_TEAMS | LOW_TIER_STARS


def is_watchlist_team(team_name):
    """
    Check if team is on watchlist (case-insensitive, fuzzy)
    """
    team_normalized = team_name.strip().lower()
    for watchlist_team in ALL_WATCHLIST_TEAMS:
        if watchlist_team.lower() in team_normalized or team_normalized in watchlist_team.lower():
            return True
    return False


def get_watchlist_info(team_name):
    """
    Get watchlist category and badge
    Returns: (category, badge) or (None, None)
    """
    team_normalized = team_name.strip().lower()
    
    # Check elite defensive first
    for elite_team in ELITE_DEFENSIVE_TEAMS:
        if elite_team.lower() in team_normalized or team_normalized in elite_team.lower():
            return ("elite", "👁️ W")
    
    # Check low-tier stars
    for star_team in LOW_TIER_STARS:
        if star_team.lower() in team_normalized or team_normalized in star_team.lower():
            return ("low_tier_star", "🔍 W")
    
    return (None, None)
