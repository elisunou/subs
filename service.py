# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs
import requests, os, sys, urllib.parse, zipfile, difflib, re, json, time

ADDON = xbmcaddon.Addon()
API_BASE = "https://api.subs.ro/v1.0"

# ============================================================================
#                           FUNCȚII UTILITARE
# ============================================================================

def log(msg, level=xbmc.LOGINFO):
    """Logging cu control prin setări"""
    if ADDON.getSetting('debug_log') == 'true':
        xbmc.log(f"[Subs.ro] {msg}", level)

def get_api_key():
    """Obține cheia API din setări - OBLIGATORIU pentru funcționare"""
    api_key = ADDON.getSetting('api_key')
    
    if not api_key or api_key.strip() == "":
        # Prima încercare: Dialog simplu
        dialog = xbmcgui.Dialog()
        api_key = dialog.input(
            "Introdu cheia ta API de la Subs.ro",
            type=xbmcgui.INPUT_ALPHANUM
        )
        
        if api_key and api_key.strip():
            ADDON.setSetting('api_key', api_key.strip())
            
            # Confirmăm salvarea
            xbmcgui.Dialog().notification(
                "Subs.ro", 
                "✓ Cheie API salvată cu succes!", 
                xbmcgui.NOTIFICATION_INFO, 
                3000
            )
            return api_key.strip()
        else:
            # Dacă user anulează, oferim opțiune de a deschide setările
            if dialog.yesno(
                "Subs.ro - Cheie API Necesară",
                "Addon-ul necesită o cheie API pentru a funcționa.\n\n"
                "Pași:\n"
                "1. Accesează https://subs.ro/api\n"
                "2. Autentifică-te cu contul tău\n"
                "3. Generează/Copiază cheia API\n\n"
                "Vrei să deschid setările acum?"
            ):
                # Deschide setările addon-ului
                xbmc.executebuiltin('Addon.OpenSettings(service.subtitles.subsro)')
            else:
                xbmcgui.Dialog().notification(
                    "Subs.ro", 
                    "Configurează cheia API în setări pentru a continua.", 
                    xbmcgui.NOTIFICATION_WARNING, 
                    5000
                )
            return None
    
    return api_key.strip()

def validate_api_key(api_key):
    """Validează cheia API prin cerere de test la /quota (conform schemei OpenAPI)"""
    try:
        headers, extra_params = get_auth(api_key)
        r = requests.get(f"{API_BASE}/quota", headers=headers, params=extra_params, timeout=5)
        
        if r.status_code == 200:
            log("Cheie API validă ✓")
            return True
        elif r.status_code == 401:
            log("Cheie API invalidă ✗", xbmc.LOGERROR)
            xbmcgui.Dialog().ok(
                "Subs.ro - Cheie API Invalidă",
                "Cheia API introdusă nu este validă.\n\n"
                "Te rog verifică:\n"
                "• Cheia a fost copiată corect (fără spații)\n"
                "• Contul de pe subs.ro este activ\n"
                "• Cheia nu a expirat\n\n"
                "Generează o cheie nouă de la:\n"
                "https://subs.ro/api"
            )
            # Șterge cheia invalidă
            ADDON.setSetting('api_key', '')
            return False
        else:
            log(f"Eroare validare API: {r.status_code}", xbmc.LOGERROR)
            return False
    except Exception as e:
        log(f"Eroare conexiune validare API: {e}", xbmc.LOGERROR)
        # Acceptăm cheia dacă avem probleme de conexiune
        return True

def handle_api_error(status_code, response=None):
    """
    Gestionează erorile API conform schemei ErrorResponse:
      { status: integer, message: string, meta: { requestId: string } }
    Încearcă să citească 'message' din body-ul răspunsului; fallback la mesaje locale.
    """
    fallback_errors = {
        400: "Cerere invalidă.",
        401: "Cheie API invalidă! Verifică setările addon-ului.",
        403: "Acces interzis sau limită de download atinsă.",
        404: "Subtitrarea nu a fost găsită.",
        429: "Prea multe cereri! Încearcă mai târziu.",
        500: "Eroare de server Subs.ro. Revenim imediat."
    }

    # Încearcă să citească mesajul din ErrorResponse body
    api_message = None
    request_id = None
    if response is not None:
        try:
            err_body = response.json()
            api_message = err_body.get('message')
            request_id  = err_body.get('meta', {}).get('requestId')
        except Exception:
            pass

    msg = api_message or fallback_errors.get(status_code, f"Eroare API necunoscută (Cod: {status_code})")

    if request_id:
        log(f"API error {status_code} | requestId={request_id} | {msg}", xbmc.LOGERROR)
    else:
        log(f"API error {status_code} | {msg}", xbmc.LOGERROR)

    xbmcgui.Dialog().notification("Eroare Subs.ro", msg, xbmcgui.NOTIFICATION_ERROR, 5000)

    if status_code == 401:
        ADDON.setSetting('api_key', '')
        ADDON.setSetting('api_key_validated', 'false')

def get_auth(api_key):
    """
    Returnează (headers, params_extra) conform schemei OpenAPI care acceptă:
      - X-Subs-Api-Key  (ApiKeyHeader) - trimis în header HTTP
      - apiKey          (ApiKeyQuery)  - trimis ca query param
    Metoda se selectează din setări; implicit: header.
    """
    auth_method = ADDON.getSetting('auth_method')  # '0' = header (default), '1' = query param
    if auth_method == '1':
        return {'Accept': 'application/json'}, {'apiKey': api_key}
    return {'X-Subs-Api-Key': api_key, 'Accept': 'application/json'}, {}

def get_params():
    """Extrage parametrii din URL"""
    param_string = sys.argv[2] if len(sys.argv) > 2 else ""
    return dict(urllib.parse.parse_qsl(param_string.lstrip('?')))

# ============================================================================
#                        FUNCȚII CACHE (NOU!)
# ============================================================================

def get_cache_path():
    """Returnează path-ul pentru cache"""
    profile_path = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    cache_dir = os.path.join(profile_path, 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir

def get_cache_key(field, value, language='ro'):
    """Generează o cheie unică pentru cache"""
    import hashlib
    cache_string = f"{field}:{value}:{language}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def load_from_cache(cache_key):
    """Încarcă rezultate din cache"""
    if ADDON.getSetting('cache_results') != 'true':
        return None
    
    cache_file = os.path.join(get_cache_path(), f"{cache_key}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    # Verifică dacă cache-ul e expirat
    cache_duration = int(ADDON.getSetting('cache_duration')) * 60  # minute -> secunde
    file_age = time.time() - os.path.getmtime(cache_file)
    
    if file_age > cache_duration:
        log(f"Cache expirat pentru {cache_key}")
        try:
            os.remove(cache_file)
        except:
            pass
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log(f"Cache hit pentru {cache_key}")
        return data
    except:
        return None

def save_to_cache(cache_key, data):
    """Salvează rezultate în cache"""
    if ADDON.getSetting('cache_results') != 'true':
        return
    
    cache_file = os.path.join(get_cache_path(), f"{cache_key}.json")
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"Salvat în cache: {cache_key}")
    except Exception as e:
        log(f"Eroare salvare cache: {e}", xbmc.LOGERROR)

# ============================================================================
#                        VERIFICARE QUOTA API (NOU!)
# ============================================================================

def check_quota():
    """
    Verifică quota API via GET /quota și afișează avertisment dacă e jos.
    Schema QuotaInfo: total_quota, used_quota, remaining_quota, quota_type, ip_address, api_key
    """
    API_KEY = get_api_key()
    if not API_KEY:
        return True
    
    try:
        headers, extra_params = get_auth(API_KEY)
        r = requests.get(f"{API_BASE}/quota", headers=headers, params=extra_params, timeout=5)
        
        if r.status_code == 200:
            data = r.json()
            quota_info = data.get('quota', {})
            
            total = quota_info.get('total_quota', 0)
            used = quota_info.get('used_quota', 0)
            remaining = quota_info.get('remaining_quota', 0)
            quota_type = quota_info.get('quota_type', 'unknown')
            
            log(f"Quota API ({quota_type}): {remaining}/{total} (folosit: {used})")
            
            # Avertisment dacă rămân sub 10%
            if total > 0 and remaining < (total * 0.1):
                xbmcgui.Dialog().notification(
                    "Subs.ro - Avertisment",
                    f"Quota rămasă: {remaining}/{total} cereri",
                    xbmcgui.NOTIFICATION_WARNING,
                    5000
                )
                return False
            
            return True
        elif r.status_code == 401:
            log("Quota: cheie API invalidă (401)", xbmc.LOGERROR)
            handle_api_error(401, r)
            return False
    except Exception as e:
        log(f"Eroare verificare quota: {e}", xbmc.LOGERROR)
        return True

# ============================================================================
#                    MATCHMAKING AVANSAT (NOU!)
# ============================================================================

def calculate_match_score(subtitle_name, video_file):
    """
    Calculează un scor de potrivire între subtitrare și video
    Returnează: (score, details)
    """
    score = 0
    details = {}
    
    sub_lower = subtitle_name.lower()
    video_lower = os.path.basename(video_file).lower()
    
    # 1. Detectare episod în ambele — normalizăm cu int() pentru a ignora zero-padding
    #    Acoperă: s05e05, s5e5, s05e5, s5e05, etc.
    episode_pattern = r's(\d+)e(\d+)'
    sub_match = re.search(episode_pattern, sub_lower)
    video_match = re.search(episode_pattern, video_lower)
    
    if sub_match and video_match:
        sub_ep   = (int(sub_match.group(1)),   int(sub_match.group(2)))
        video_ep = (int(video_match.group(1)), int(video_match.group(2)))
        if sub_ep == video_ep:
            score += 100
            details['episode_match'] = True
        else:
            score -= 50
            details['episode_match'] = False
    
    # 2. Detectare rezoluție (2160p/4K, 1080p, 720p) — +40 dacă identică, -30 dacă diferită
    if ADDON.getSetting('match_resolution') == 'true':
        def detect_resolution(name):
            """Detectează rezoluția dintr-un nume de fișier, evitând coliziuni substring."""
            # Ordine importantă: de la mai specific la mai general
            if re.search(r'(?<![a-z])(2160p|4320p)(?![a-z0-9])', name):
                return '2160p'
            if re.search(r'(?<![a-z])4k(?![a-z0-9])', name):
                return '2160p'
            if re.search(r'(?<![a-z])uhd(?![a-z0-9])', name):
                return '2160p'
            if re.search(r'(?<![a-z])(1080p|1080i|fhd)(?![a-z0-9])', name):
                return '1080p'
            if re.search(r'(?<![a-z])720p(?![a-z0-9])', name):
                return '720p'
            if re.search(r'(?<![a-z])480p(?![a-z0-9])', name):
                return '480p'
            return None

        video_res = detect_resolution(video_lower)
        sub_res   = detect_resolution(sub_lower)
        
        if video_res and sub_res:
            if video_res == sub_res:
                score += 40
                details['resolution_match'] = True
            else:
                score -= 30
                details['resolution_match'] = False
        details['video_resolution'] = video_res or 'unknown'
        details['sub_resolution']   = sub_res   or 'unknown'
    
    # 3. Detectare sursă (BluRay, WEB-DL, HDTV)
    sources = {
        'bluray': ['bluray', 'bdrip', 'brrip', 'remux'],
        'web':    ['web-dl', 'webrip', 'webdl', 'amzn', 'nf', 'netflix'],
        'hdtv':   ['hdtv', 'pdtv']
    }
    
    video_source = None
    sub_source   = None
    
    for src_type, keywords in sources.items():
        if any(k in video_lower for k in keywords):
            video_source = src_type
        if any(k in sub_lower for k in keywords):
            sub_source = src_type
    
    if video_source and sub_source:
        if video_source == sub_source:
            score += 50
            details['source_match'] = True
        else:
            score -= 20
    
    # 4. Detectare release group
    video_group = re.search(r'-([a-z0-9]+)(?:\.[a-z0-9]+)?$', video_lower)
    sub_group   = re.search(r'-([a-z0-9]+)(?:\.[a-z0-9]+)?$', sub_lower)
    
    if video_group and sub_group:
        if video_group.group(1) == sub_group.group(1):
            score += 30
            details['group_match'] = True
    
    # 5. Similaritate generală (difflib)
    video_name = os.path.splitext(os.path.basename(video_file))[0].lower()
    sub_name   = os.path.splitext(subtitle_name)[0].lower()
    similarity = difflib.SequenceMatcher(None, video_name, sub_name).ratio()
    score += int(similarity * 20)
    details['similarity'] = similarity
    
    # 6. Traducător prioritar
    priority_translators = ['subrip', 'retail', 'netflix', 'hbo', 'amazon']
    if any(t in sub_lower for t in priority_translators):
        score += 15
        details['priority_translator'] = True
    
    return score, details

def sort_subtitles_by_match(items, video_file):
    """Sortează subtitlările după scor de potrivire"""
    scored_items = []
    
    for item in items:
        title = item.get('title', '')
        score, details = calculate_match_score(title, video_file)
        item['match_score'] = score
        item['match_details'] = details
        scored_items.append(item)
    
    # Sortare descrescătoare după scor
    scored_items.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    log(f"Top 3 potriviri:")
    for i, item in enumerate(scored_items[:3]):
        log(f"  #{i+1} (Scor: {item['match_score']:+d}): {item['title'][:60]}")
    
    return scored_items

# ============================================================================
#                    FILTRARE AVANSATĂ (NOU!)
# ============================================================================

def filter_subtitles(items, video_info):
    """Aplică filtre conform setărilor utilizatorului"""
    filtered = items[:]
    
    # Filtru: Exclude hearing impaired
    if ADDON.getSetting('filter_by_hearing_impaired') == 'true':
        filtered = [item for item in filtered 
                   if 'hearing' not in item.get('title', '').lower() 
                   and 'sdh' not in item.get('title', '').lower()]
        log(f"După filtrare hearing impaired: {len(filtered)} subtitrări")
    
    # Filtru: Rating minim
    min_rating = int(ADDON.getSetting('min_rating'))
    if min_rating > 0:
        # Notă: API-ul nu returnează rating, dar poți adăuga logica aici
        pass
    
    return filtered

# ============================================================================
#                    FORMATARE LABEL CU BADGE-URI (NOU!)
# ============================================================================

def format_label_with_badges(item, show_score=False):
    """Formatează label-ul cu badge-uri colorate"""
    title = item.get('title', 'Unknown')
    badges = []
    
    details = item.get('match_details', {})
    
    if details.get('episode_match'):
        badges.append('[COLOR lime]✓EP[/COLOR]')
    if details.get('resolution_match'):
        res = details.get('video_resolution', '').upper()
        badges.append(f'[COLOR aqua]✓{res}[/COLOR]')
    elif details.get('resolution_match') is False:
        badges.append('[COLOR red]✗RES[/COLOR]')
    if details.get('source_match'):
        badges.append('[COLOR cyan]✓SRC[/COLOR]')
    if details.get('group_match'):
        badges.append('[COLOR yellow]✓GRP[/COLOR]')
    if details.get('priority_translator'):
        badges.append('[COLOR gold]★[/COLOR]')
    
    label = ' '.join(badges) + ' ' + title if badges else title
    
    if show_score and 'match_score' in item:
        label = f"[{item['match_score']:+d}] {label}"
    
    return label

# ============================================================================
#                        CĂUTARE SUBTITRĂRI
# ============================================================================

def search_subtitles():
    """Caută subtitrări cu matchmaking și cache"""
    API_KEY = get_api_key()
    if not API_KEY:
        return
    
    # VALIDARE API KEY la prima utilizare
    if ADDON.getSetting('api_key_validated') != 'true':
        log("Validare API key...")
        if validate_api_key(API_KEY):
            ADDON.setSetting('api_key_validated', 'true')
        else:
            return
    
    # Verifică quota periodic
    if ADDON.getSetting('check_quota') == 'true':
        check_quota()
    
    handle = int(sys.argv[1])
    player = xbmc.Player()
    if not player.isPlayingVideo():
        return

    info = player.getVideoInfoTag()
    video_file = player.getPlayingFile()
    imdb_id = info.getIMDBNumber()
    tvshow = info.getTVShowTitle()
    season = info.getSeason()
    episode = info.getEpisode()
    title = info.getTitle() or xbmc.getInfoLabel('VideoPlayer.Title')

    # Determină câmpul de căutare conform schemei: imdbid | tmdbid | title | release
    tmdb_id = info.getDbId() if hasattr(info, 'getDbId') else None
    if imdb_id and imdb_id.startswith('tt'):
        field, value = "imdbid", imdb_id
    elif tmdb_id and str(tmdb_id).isdigit() and int(tmdb_id) > 0:
        field, value = "tmdbid", str(tmdb_id)
    else:
        field = "title"
        value = f"{tvshow} S{str(season).zfill(2)}E{str(episode).zfill(2)}" if tvshow and season != -1 else title

    # Limbă din setări (enum: ro, en, ita, fra, ger, ung, gre, por, spa, alt)
    lang_map = {'0': 'ro', '1': 'en', '2': 'ita', '3': 'fra', '4': 'ger',
                '5': 'ung', '6': 'gre', '7': 'por', '8': 'spa', '9': 'alt'}
    lang_setting = ADDON.getSetting('search_language') or '0'
    language = lang_map.get(lang_setting, 'ro')

    # Verifică cache-ul
    cache_key = get_cache_key(field, value, language)
    cached_data = load_from_cache(cache_key)
    
    if cached_data:
        log("Folosesc date din cache")
        data = cached_data
    else:
        # Cerere API: GET /search/{searchField}/{value}?language=...
        url = f"{API_BASE}/search/{field}/{urllib.parse.quote(str(value))}"
        headers, extra_params = get_auth(API_KEY)
        query_params = {'language': language, **extra_params}

        try:
            r = requests.get(url, params=query_params, headers=headers,
                             timeout=int(ADDON.getSetting('timeout_duration') or 10))
            
            if r.status_code != 200:
                handle_api_error(r.status_code, r)
                return

            data = r.json()
            log(f"Răspuns API: status={data.get('status')}, count={data.get('count', 0)}, requestId={data.get('meta', {}).get('requestId', '')}")
            
            # Salvează în cache doar dacă răspunsul e valid
            if data.get('status') == 200:
                save_to_cache(cache_key, data)
        
        except Exception as e:
            log(f"Eroare căutare: {e}", xbmc.LOGERROR)
            xbmcplugin.endOfDirectory(handle)
            return

    if data.get('status') == 200:
        items = data.get('items', [])
        count = data.get('count', len(items))
        log(f"Total subtitrări găsite: {count}")
        
        if not items:
            xbmcgui.Dialog().notification("Subs.ro", "Nu s-au găsit subtitrări", xbmcgui.NOTIFICATION_INFO, 3000)
            xbmcplugin.endOfDirectory(handle)
            return
        
        # Aplică filtre
        items = filter_subtitles(items, {'video_file': video_file})
        
        # Sortare prin matchmaking
        if ADDON.getSetting('enable_matchmaking') == 'true':
            items = sort_subtitles_by_match(items, video_file)
        
        # Afișare cu badge-uri
        show_scores = ADDON.getSetting('show_match_scores') == 'true'
        
        for item in items:
            # SubtitleItem fields (schema): id(int), createdAt, updatedAt, description,
            #   link, downloadLink, title, year(int), imdbid, tmdbid(int),
            #   poster, translator, language, type(movie|series)
            item_id         = int(item.get('id', 0))          # schema: integer
            item_title      = item.get('title', 'Unknown Release')
            item_year       = item.get('year', '')             # schema: integer
            item_lang       = item.get('language', 'ro').upper()
            item_type       = item.get('type', '')             # enum: movie | series
            item_translator = item.get('translator', 'N/A')
            item_poster     = item.get('poster', '')
            item_imdbid     = item.get('imdbid', '')
            item_tmdbid     = item.get('tmdbid', '')           # schema: integer
            item_desc       = item.get('description', '')
            item_link       = item.get('link', '')             # URL pagină subtitrare
            item_dl_link    = item.get('downloadLink', '')     # URL direct download (din schemă)

            if ADDON.getSetting('enable_matchmaking') == 'true':
                label = format_label_with_badges(item, show_scores)
            else:
                label = item_title
            
            list_item = xbmcgui.ListItem(label=label, label2=label)
            list_item.setArt({'thumb': item_poster, 'icon': 'logo.png'})
            
            # Informații suplimentare în plot
            plot_lines = [
                item_title + (f" ({item_year})" if item_year else ''),
                f"Tip: {'Film' if item_type == 'movie' else 'Serial' if item_type == 'series' else item_type}",
                f"Traducător: {item_translator}",
                f"Limba: {item_lang}",
            ]
            if item_imdbid:
                plot_lines.append(f"IMDb: {item_imdbid}")
            if item_tmdbid:
                plot_lines.append(f"TMDb: {item_tmdbid}")
            if item_desc:
                plot_lines.append(item_desc)
            if item_link:
                plot_lines.append(f"Link: {item_link}")
            
            if 'match_score' in item:
                plot_lines.insert(1, f"Scor potrivire: {item['match_score']}")
            
            list_item.setInfo('video', {
                'title': label,
                'plot': '\n'.join(plot_lines),
                'tagline': item_translator,
                'year': int(item_year) if str(item_year).isdigit() else 0
            })
            
            # Pasăm id-ul (integer) și downloadLink-ul din schemă către acțiunea de download
            cmd = f"{sys.argv[0]}?action=download&id={item_id}"
            if item_dl_link:
                cmd += f"&dl={urllib.parse.quote(item_dl_link, safe='')}"
            xbmcplugin.addDirectoryItem(handle=handle, url=cmd, listitem=list_item, isFolder=False)
    
    xbmcplugin.endOfDirectory(handle)

# ============================================================================
#                        DESCĂRCARE SUBTITRARE
# ============================================================================

def download_subtitle(sub_id, download_link=None):
    """
    Descarcă și activează subtitrarea.
    Endpoint primar:  GET /subtitle/{id}/download → application/octet-stream
    Fallback:         downloadLink din SubtitleItem dacă e furnizat de API
    Schema: {id} este integer.
    """
    API_KEY = get_api_key()
    if not API_KEY:
        return
    
    # id trebuie să fie integer conform schemei
    try:
        sub_id_int = int(sub_id)
    except (TypeError, ValueError):
        log(f"ID subtitrare invalid: {sub_id}", xbmc.LOGERROR)
        return

    headers, extra_params = get_auth(API_KEY)
    # Endpoint-ul returnează binar (application/octet-stream), nu JSON
    headers.pop('Accept', None)

    # Folosim downloadLink din SubtitleItem dacă e disponibil,
    # altfel construim URL-ul standard: GET /subtitle/{id}/download
    if download_link:
        url = download_link
        log(f"Download via downloadLink din SubtitleItem: {url}")
    else:
        url = f"{API_BASE}/subtitle/{sub_id_int}/download"
        log(f"Download via endpoint standard: {url}")
    
    player = xbmc.Player()
    tmp_path = xbmcvfs.translatePath("special://temp/")
    archive = os.path.join(tmp_path, "subs_download.zip")
    target_srt = os.path.join(tmp_path, "forced.romanian.subsro.srt")

    try:
        r = requests.get(url, headers=headers, params=extra_params, timeout=15)
        
        if r.status_code != 200:
            handle_api_error(r.status_code, r)
            return
            
        with open(archive, "wb") as f:
            f.write(r.content)
        
        with zipfile.ZipFile(archive, 'r') as z:
            srts = sorted([f for f in z.namelist() if f.lower().endswith(('.srt', '.ass'))])
            if not srts:
                return
            
            # Gestionare episoade multiple
            multi_handling = ADDON.getSetting('multi_episode_handling')
            
            if len(srts) > 1:
                if multi_handling == '0':  # Selectare manuală
                    dialog = xbmcgui.Dialog()
                    display_names = [os.path.basename(f) for f in srts]
                    selected = dialog.select("Alege episodul:", display_names)
                    if selected == -1:
                        return
                    f_name = srts[selected]
                elif multi_handling == '1':  # Prima subtitrare
                    f_name = srts[0]
                else:  # Cea mai potrivită (matchmaking)
                    video_file = player.getPlayingFile()
                    best_srt = srts[0]
                    best_score = -999
                    
                    for srt in srts:
                        score, _ = calculate_match_score(os.path.basename(srt), video_file)
                        if score > best_score:
                            best_score = score
                            best_srt = srt
                    
                    f_name = best_srt
                    log(f"Selectat automat: {os.path.basename(f_name)} (Scor: {best_score})")
            else:
                f_name = srts[0]
            
            # Conversie encoding
            content = z.read(f_name)
            encoding_priority = int(ADDON.getSetting('encoding_priority'))
            
            encodings = ['utf-8', 'iso-8859-2', 'windows-1250', 'latin1']
            if encoding_priority > 0:
                # Rotește lista conform priorității
                encodings = encodings[encoding_priority:] + encodings[:encoding_priority]
            
            text = None
            for enc in encodings:
                try:
                    text = content.decode(enc)
                    log(f"Encoding detectat: {enc}")
                    break
                except:
                    continue
            
            if not text:
                text = content.decode('latin1', errors='ignore')
            
            with open(target_srt, "w", encoding="utf-8") as f:
                f.write(text)

        xbmc.executebuiltin("Dialog.Close(subtitlesearch)")
        xbmc.sleep(500)
        player.setSubtitles(target_srt)
        
        # Activare forțată
        for _ in range(15):
            if not player.isPlayingVideo():
                break
            streams = player.getAvailableSubtitleStreams()
            for i, s_name in enumerate(streams):
                if "forced.romanian" in s_name.lower() or "external" in s_name.lower():
                    if player.getSubtitleStream() != i:
                        player.setSubtitleStream(i)
                        player.showSubtitles(True)
            xbmc.sleep(400)

        # Notificare
        if ADDON.getSetting('notify_auto_download') == 'true':
            duration = int(ADDON.getSetting('notify_duration')) * 1000
            xbmcgui.Dialog().notification(
                "Subs.ro",
                "Activat: " + os.path.basename(f_name)[:30],
                xbmcgui.NOTIFICATION_INFO,
                duration
            )

    except Exception as e:
        log(f"Eroare download: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Subs.ro", "Eroare la descărcare", xbmcgui.NOTIFICATION_ERROR, 3000)

# ============================================================================
#                            ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    p = get_params()
    if p.get('action') == 'download':
        # 'dl' = downloadLink din SubtitleItem (opțional, URL direct din schemă)
        dl_encoded = p.get('dl', '')
        dl_url = urllib.parse.unquote(dl_encoded) if dl_encoded else None
        download_subtitle(p.get('id'), download_link=dl_url)
    else:
        search_subtitles()
