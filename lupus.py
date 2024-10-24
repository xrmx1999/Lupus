import logging
import random
from collections import Counter

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup, 
)

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Abilita il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Il tuo token del bot
TOKEN = "7750321079:AAENQ7e959v72mbKQpu1W1APVdIJIYi6BsA" 


# Dizionario per memorizzare lo stato del gioco
game_state = {}


# Handler per il comando /start (modificato)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Crea la tastiera iniziale
    keyboard = [
        [KeyboardButton("Nuova partita")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Benvenuto nel bot di Lupus in Tabula!",
        reply_markup=reply_markup)

# Handler per il comando /endgame
async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Verifica se la partita esiste e se l'utente è il creatore
    if chat_id in game_state and user.id == game_state[chat_id].get(
            "creator_id"):
        await context.bot.send_message(chat_id=chat_id,
                                       text="Partita terminata!")
        del game_state[chat_id]  # Elimina la partita dallo stato del gioco
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=
            "Non hai il permesso di terminare questa partita o la partita non esiste."
        )
        

# Handler per il comando /eliminati
async def eliminati(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in game_state:
        eliminated_players = []
        for player in game_state[chat_id]["roles"].keys():
            if player not in game_state[chat_id]["players"]:
                eliminated_players.append(player)

        if eliminated_players:
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                f"Giocatori eliminati: {', '.join(eliminated_players)}")
        else:
            await context.bot.send_message(chat_id=chat_id,
                                           text="Nessun giocatore eliminato.")
    else:
        await context.bot.send_message(chat_id=chat_id,
                                       text="Nessuna partita in corso.")


# Handler per il comando /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in game_state:
        phase = game_state[chat_id]["phase"]
        night_count = game_state[chat_id].get("night_count", 0)
        alive_players = game_state[chat_id]["players"]

        status_message = f"Fase di gioco: {phase}\n"
        if phase == "night":
            status_message += f"Notte numero: {night_count}\n"
        status_message += f"Giocatori in vita: {', '.join(alive_players)}"

        await context.bot.send_message(chat_id=chat_id,
                                       text=status_message)
    else:
        await context.bot.send_message(chat_id=chat_id,
                                       text="Nessuna partita in corso.")


# Handler per la nuova partita (modificato)
async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game_state[chat_id] = {
        "players": [],
        "roles": [],
        "phase": "registration",
        "selected_roles": [],
        "creator_id": user.id  # Salva l'ID del creatore
    }

    # Invia la tastiera per aggiungere giocatori solo al creatore in privato
    keyboard = [[KeyboardButton("Aggiungi giocatore")],
                [KeyboardButton("Inizia selezione ruoli")]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user.id,
                                   text="Nuova partita creata!",
                                   reply_markup=reply_markup)


# Handler per aggiungere un giocatore (modificato)
async def addplayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    # Verifica se l'utente è il creatore della partita
    if user.id != game_state[chat_id].get("creator_id"):
        return  # Ignora il messaggio se non è il creatore
    if game_state[chat_id]["phase"] != "registration":
        await context.bot.send_message(
            chat_id=chat_id,
            text="Non puoi aggiungere giocatori durante la partita.")
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=
        "Invia il nome utente del giocatore che vuoi aggiungere (es. @nomeutente):"
    )

    # Imposta uno stato per aspettare il nome utente
    game_state[chat_id]["waiting_for_player"] = True


# Handler per iniziare la selezione dei ruoli (modificato)
async def start_role_selection(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    # Verifica se l'utente è il creatore della partita
    if user.id != game_state[chat_id].get("creator_id"):
        return  # Ignora il messaggio se non è il creatore
    if game_state[chat_id]["phase"] != "registration":
        await context.bot.send_message(
            chat_id=chat_id, text="Non puoi selezionare i ruoli ora.")
        return

    if len(game_state[chat_id]["players"]) < 5:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Hai bisogno di almeno 5 giocatori per iniziare la partita.")
        return

    # Crea la tastiera con i ruoli
    keyboard = [
        [
            KeyboardButton("Contadino"),
            KeyboardButton("Lupo"),
            KeyboardButton("Veggente")
        ],
        [
            KeyboardButton("Guardia del Corpo"),
            KeyboardButton("Gufo"),
            KeyboardButton("Medium")
        ],
        [KeyboardButton("Mitomane"), KeyboardButton("Fine selezione")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="Seleziona i ruoli usando la tastiera qui sotto:",
        reply_markup=reply_markup)


# Handler per i messaggi di testo (modificato)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    user = update.effective_user

    if game_state[chat_id]["phase"] == "registration":
        # Verifica se l'utente è il creatore della partita
        if user.id != game_state[chat_id].get("creator_id"):
            return  # Ignora il messaggio se non è il creatore
        if "waiting_for_player" in game_state[chat_id] and game_state[chat_id][
                "waiting_for_player"]:
            player = text  # Il testo è il nome utente
            if player in game_state[chat_id]["players"]:
                await context.bot.send_message(
                    chat_id=chat_id, text=f"{player} è già nella partita.")
            else:
                game_state[chat_id]["players"].append(player)
                await context.bot.send_message(chat_id=chat_id, text=f"{player} aggiunto alla partita.")

            # Mostra la lista dei giocatori
            players_list = ", ".join(game_state[chat_id]["players"])
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Giocatori attuali: {players_list}")

            # Mantieni la tastiera per aggiungere giocatori
            keyboard = [
                [KeyboardButton("Aggiungi giocatore")],
                [KeyboardButton("Inizia selezione ruoli")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=chat_id,
                text="Aggiungi un altro giocatore o inizia la selezione dei ruoli:",
                reply_markup=reply_markup)

            del game_state[chat_id]["waiting_for_player"]
        elif text in RUOLI:
            game_state[chat_id]["selected_roles"].append(RUOLI[text])
            await context.bot.send_message(
                chat_id=chat_id, text=f"Ruolo {text} aggiunto!")
        elif text == "Fine selezione":
            # Controlla se ci sono abbastanza ruoli
            if len(game_state[chat_id]["selected_roles"]) < len(
                    game_state[chat_id]["players"]):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=
                    "Non hai selezionato abbastanza ruoli per tutti i giocatori."
                )
                return

            game_state[chat_id]["roles"] = game_state[chat_id][
                "selected_roles"]
            del game_state[chat_id]["selected_roles"]
            game_state[chat_id]["phase"] = "night"
            await context.bot.send_message(
                chat_id=chat_id,
                text="Ruoli selezionati! La partita è iniziata! È notte...")

            # Assegna i ruoli ai giocatori in modo casuale
            assign_roles(chat_id, context)

        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Comando non valido. Per favore, usa la tastiera per selezionare i ruoli."
            )
    elif game_state[chat_id]["phase"] == "night":
        # Gestione azioni notturne
        await handle_night_action(update, context)
        
        
# Funzione per gestire le azioni notturne
async def handle_night_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Verifica se l'utente è un lupo e non ha ancora votato
    if RUOLI["Lupo"] in game_state[chat_id]["roles"].values() and not game_state[chat_id].get("wolves_voted", False):
        # Crea la tastiera con i giocatori per il voto dei lupi
        keyboard = []
        for player in game_state[chat_id]["players"]:
            # Escludi il lupo stesso dalla lista dei giocatori votabili
            if game_state[chat_id]["roles"][player] != RUOLI["Lupo"]:  
                keyboard.append([InlineKeyboardButton(player, callback_data=f"vote_{player}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user.id,  # Invia il messaggio in privato al lupo
                                       text="Sei un lupo! Vota per la vittima:",
                                       reply_markup=reply_markup)
        # Imposta lo stato per indicare che i lupi hanno votato
        game_state[chat_id]["wolves_voted"] = True
        
    # Gestione azione del Veggente
    if RUOLI["Veggente"] in game_state[chat_id]["roles"].values() and not game_state[chat_id].get("seer_acted", False):
        # Crea la tastiera con i giocatori per l'indagine del Veggente
        keyboard = []
        for player in game_state[chat_id]["players"]:
            keyboard.append([InlineKeyboardButton(player, callback_data=f"investigate_{player}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user.id,  # Invia il messaggio in privato al Veggente
                                       text="Sei il Veggente! Scegli un giocatore da investigare:",
                                       reply_markup=reply_markup)
        game_state[chat_id]["seer_acted"] = True
        
    # Gestione azione della Guardia del Corpo
    if RUOLI["Guardia del Corpo"] in game_state[chat_id]["roles"].values() and not game_state[chat_id].get("bodyguard_acted", False):
        # Crea la tastiera con i giocatori per la protezione della Guardia del Corpo
        keyboard = []
        for player in game_state[chat_id]["players"]:
            keyboard.append([InlineKeyboardButton(player, callback_data=f"protect_{player}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user.id,  # Invia il messaggio in privato alla Guardia del Corpo
                                       text="Sei la Guardia del Corpo! Scegli un giocatore da proteggere:",
                                       reply_markup=reply_markup)
        game_state[chat_id]["bodyguard_acted"] = True
    
    # Gestione azione del Gufo
    if RUOLI["Gufo"] in game_state[chat_id][
            "roles"].values() and not game_state[chat_id].get(
                "owl_acted", False):
        # Crea la tastiera con i giocatori per la scelta del Gufo
        keyboard = []
        for player in game_state[chat_id]["players"]:
            keyboard.append(
                [InlineKeyboardButton(player, callback_data=f"owl_{player}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=user.id,  # Invia il messaggio in privato al Gufo
            text="Sei il Gufo! Scegli un giocatore da 'gufare':",
            reply_markup=reply_markup)
        game_state[chat_id]["owl_acted"] = True
        
    # Gestione azione del Medium (solo dalla seconda notte in poi)
    if game_state[chat_id]["night_count"] > 1 and RUOLI["Medium"] in game_state[chat_id]["roles"].values() and not game_state[chat_id].get("medium_acted", False):
        # Crea la tastiera con i giocatori per la scelta del Medium
        keyboard = []
        for player in game_state[chat_id]["players"]:
            keyboard.append([InlineKeyboardButton(player, callback_data=f"contact_{player}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user.id,  # Invia il messaggio in privato al Medium
                                       text="Sei il Medium! Scegli un giocatore di cui vuoi conoscere la fazione (se è ancora vivo, 'fantasma' altrimenti):",
                                       reply_markup=reply_markup)
        game_state[chat_id]["medium_acted"] = True    
        
    # Controlla se tutti i ruoli con azioni notturne hanno agito
    if all_night_actions_completed(chat_id):
        await end_night(update, context)  # Termina la notte        


# Funzione per verificare se tutte le azioni notturne sono state completate
def all_night_actions_completed(chat_id):
    # Controlla se i lupi hanno votato, se il Veggente ha agito, se la Guardia del Corpo ha agito e se il Gufo ha agito
    wolves_voted = game_state[chat_id].get("wolves_voted", False)
    seer_acted = game_state[chat_id].get("seer_acted", False)
    bodyguard_acted = game_state[chat_id].get("bodyguard_acted", False)
    owl_acted = game_state[chat_id].get("owl_acted", False)
    copycat_acted = game_state[chat_id].get("copycat_acted", False)
    medium_acted = game_state[chat_id].get("medium_acted", False)

    # Controlla se il Mitomane ha agito (solo se è presente nella partita)
    if RUOLI["Mitomane"] in game_state[chat_id]["roles"].values():
        copycat_acted = game_state[chat_id].get("copycat_acted", False)
    else:
        copycat_acted = True  # Se il Mitomane non è in gioco, consideriamo la sua azione come completata

    # Controlla se il Medium ha agito (solo se è presente nella partita e dalla seconda notte in poi)
    if game_state[chat_id]["night_count"] > 1 and RUOLI["Medium"] in game_state[chat_id]["roles"].values():
        medium_acted = game_state[chat_id].get("medium_acted", False)
    else:
        medium_acted = True  # Se il Medium non è in gioco o è la prima notte, consideriamo la sua azione come completata

    return wolves_voted and seer_acted and bodyguard_acted and owl_acted and copycat_acted and medium_acted


# Funzione per iniziare la votazione diurna
async def start_day_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    summary = ""  # Inizializza la stringa di riepilogo

    # Crea la tastiera con i giocatori per la votazione (escluso il "gufato")
    keyboard = []
    for player in game_state[chat_id]["roles"].keys():  # Includi tutti i giocatori, anche quelli morti
        if "owled_player" not in game_state[chat_id] or player != game_state[chat_id]["owled_player"]:
            # Escludi il Gufo se è stato "gufato"
            if game_state[chat_id]["roles"][player] != RUOLI["Gufo"] or "owled_player" not in game_state[chat_id]:  
                keyboard.append([InlineKeyboardButton(player, callback_data=f"dayvote_{player}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Annuncia il giocatore 'gufato' (se presente)
    if "owled_player" in game_state[chat_id]:
        owled_player = game_state[chat_id]["owled_player"]
        await context.bot.send_message(
            chat_id=chat_id,
            text=
            f"{owled_player} è stato 'gufato' e andrà al patibolo! Votate per chi mandare al patibolo con lui.",
            reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Votazione diurna: scegliete chi eliminare.",
            reply_markup=reply_markup)
            
    # Elimina il giocatore con più voti (se non c'è stato uno spareggio)
    if "tie_breaker" not in game_state[chat_id]:
        victim = most_voted_players[0]
        summary += f"- {victim} è stato eliminato dalla votazione.\n"
        game_state[chat_id]["players"].remove(victim)
        del game_state[chat_id]["roles"][victim]

        # Resetta i voti diurni
        game_state[chat_id]["day_votes"] = {}

        # Controlla se la partita è finita
        await check_game_end(update, context)

        # Se la partita non è finita, passa alla notte successiva
        if game_state[chat_id]["phase"] != "end":
            await start_night(update, context)

    # Invia il riepilogo degli eventi diurni
    if summary:
        await context.bot.send_message(
            chat_id=chat_id, text=f"Riepilogo del giorno:\n{summary}")       
     

# Funzione per terminare la notte e iniziare il giorno (modificata)
async def end_night(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    summary = ""  # Inizializza la stringa di riepilogo

    # Annuncia la vittima (se presente)
    if "votes" in game_state[chat_id] and game_state[chat_id]["votes"]:
        victim = max(game_state[chat_id]["votes"],
                     key=game_state[chat_id]["votes"].get)

        # Controlla se la Guardia del Corpo ha protetto la vittima
        if "protected_player" in game_state[chat_id] and game_state[chat_id][
                "protected_player"] == victim:
            summary += "- I lupi hanno attaccato un giocatore, ma è stato protetto dalla Guardia del Corpo!\n"
            victim = None  # Nessuno viene eliminato
        else:
            summary += f"- I lupi hanno ucciso {victim}!\n"
            game_state[chat_id]["players"].remove(victim)
            del game_state[chat_id]["roles"][victim]

    # Annuncia il giocatore 'gufato' (se presente)
    if "owled_player" in game_state[chat_id]:
        owled_player = game_state[chat_id]["owled_player"]
        summary += f"- Il Gufo ha mandato al patibolo {owled_player}.\n"

    # Resetta i voti, lo stato wolves_voted e protected_player
    game_state[chat_id]["votes"] = {}
    game_state[chat_id]["wolves_voted"] = False
    game_state[chat_id].pop("protected_player", None)

    # Passa alla fase diurna e inizia la votazione
    game_state[chat_id]["phase"] = "day"
    await start_day_vote(update, context)  # Chiama la funzione per iniziare la votazione

    # Invia il riepilogo degli eventi notturni
    if summary:
        await context.bot.send_message(chat_id=chat_id,
                                       text=f"Riepilogo della notte:\n{summary}")



# Handler per i callback dei pulsanti
async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = update.callback_query
    action, player = query.data.split("_")

    if action == "vote":
        # Registra il voto del lupo
        game_state[chat_id]["votes"] = game_state[chat_id].get("votes", {})
        game_state[chat_id]["votes"][player] = game_state[chat_id]["votes"].get(player, 0) + 1
        
        await query.answer(text=f"Hai votato per {player}")
        
        # Controlla se tutti i lupi hanno votato
        if len(game_state[chat_id]["votes"]) == len([role for role in game_state[chat_id]["roles"].values() if role == RUOLI["Lupo"]]):
            # Determina la vittima in base ai voti
            victim = max(game_state[chat_id]["votes"], key=game_state[chat_id]["votes"].get)
            await context.bot.send_message(chat_id=chat_id, text=f"{victim} è stato ucciso dai lupi!")
            # Resetta i voti e lo stato wolves_voted
            game_state[chat_id]["votes"] = {}
            game_state[chat_id]["wolves_voted"] = False
            # Qui andrebbe implementata la logica per passare al giorno successivo
            await end_night(update, context)  # Termina la notte
            
    elif action == "dayvote":
        # Registra il voto diurno
        game_state[chat_id]["day_votes"] = game_state[chat_id].get(
            "day_votes", {})
        game_state[chat_id]["day_votes"][player] = game_state[chat_id][
            "day_votes"].get(player, 0) + 1

        await query.answer(text=f"Hai votato per {player}")

        # Controlla se tutti i giocatori hanno votato
        if len(game_state[chat_id]["day_votes"]) == len(
                game_state[chat_id]["players"]):
            await end_day_vote(update, context)  # Termina la votazione diurna
            
    elif action == "tiebreak":
        # Registra il voto di spareggio
        game_state[chat_id]["tie_breaker_votes"] = game_state[chat_id].get(
            "tie_breaker_votes", {})
        game_state[chat_id]["tie_breaker_votes"][player] = game_state[
            chat_id]["tie_breaker_votes"].get(player, 0) + 1

        await query.answer(text=f"Hai votato per {player}")

        # Controlla se tutti i giocatori hanno votato
        if len(game_state[chat_id]["tie_breaker_votes"]) == len(
                game_state[chat_id]["players"]) - len(
                    game_state[chat_id]["tie_breaker"]):
            await end_tie_breaker_vote(update, context)
    
    elif action == "othervote":
        # Registra il voto degli altri giocatori
        game_state[chat_id]["tie_breaker_votes"] = game_state[chat_id].get(
            "tie_breaker_votes", {})
        game_state[chat_id]["tie_breaker_votes"][player] = game_state[
            chat_id]["tie_breaker_votes"].get(player, 0) + 1

        await query.answer(text=f"Hai votato per {player}")

        # Controlla se tutti gli altri giocatori hanno votato
        if len(game_state[chat_id]["tie_breaker_votes"]) == len(
                game_state[chat_id]["players"]) - len(
                    game_state[chat_id]["tie_breaker"]) - 1:  # -1 per escludere il Gufo
            await end_tie_breaker_vote(update, context)    
    
    elif action == "investigate":
        # Gestione azione del Veggente
        target_role = game_state[chat_id]["roles"][player]
        if target_role == RUOLI["Lupo"]:
            result = "Lupo"
        else:
            result = "Umano"
        await query.answer()  # Conferma la ricezione dell'azione
        await context.bot.send_message(chat_id=query.from_user.id, text=f"{player} è un {result}!")

    elif action == "protect":
        # Gestione azione della Guardia del Corpo
        game_state[chat_id]["protected_player"] = player
        await query.answer(text=f"Hai protetto {player}!")

    elif action == "owl":
        # Gestione azione del Gufo
        game_state[chat_id]["owled_player"] = player
        await query.answer(text=f"Hai 'gufato' {player}!")

    elif action == "copy":
        # Gestione azione del Mitomane
        target_role = game_state[chat_id]["roles"][player]
        copycat_player = query.from_user.id

        if target_role == RUOLI["Lupo"]:
            game_state[chat_id]["roles"][
                copycat_player] = RUOLI["Lupo"]  # Copia il ruolo del Lupo
            await query.answer(
                text=f"Hai copiato il ruolo di {player}! Ora sei un Lupo!")
            await context.bot.send_message(chat_id=copycat_player,
                                           text=f"Ora sei un Lupo!")
        elif target_role == RUOLI["Veggente"]:
            game_state[chat_id]["roles"][
                copycat_player] = RUOLI["Veggente"]  # Copia il ruolo del Veggente
            await query.answer(
                text=
                f"Hai copiato il ruolo di {player}! Ora sei un Veggente!")
            await context.bot.send_message(chat_id=copycat_player,
                                           text=f"Ora sei un Veggente!")
        else:
            game_state[chat_id]["roles"][
                copycat_player] = RUOLI[
                    "Contadino"]  # Diventa un Contadino
            await query.answer(
                text=
                f"Hai copiato il ruolo di {player}! Ora sei un Contadino!")
            await context.bot.send_message(chat_id=copycat_player,
                                           text=f"Ora sei un Contadino!")

    elif action == "contact":
        # Gestione azione del Medium
        if player in game_state[chat_id]["players"]:
            target_role = game_state[chat_id]["roles"][player]
            faction = target_role["fazione"]
            await query.answer()
            await context.bot.send_message(chat_id=query.from_user.id, text=f"{player} è della fazione {faction}!")
        else:
            await query.answer()
            await context.bot.send_message(chat_id=query.from_user.id, text=f"{player} è un fantasma!")

        # Controlla se tutte le azioni notturne sono state completate
        if all_night_actions_completed(chat_id):
            await end_night(update, context)  # Termina la notte  

# Funzione per terminare la votazione di spareggio
async def end_tie_breaker_vote(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Determina il giocatore con più voti nello spareggio
    victim = max(game_state[chat_id]["tie_breaker_votes"],
                 key=game_state[chat_id]["tie_breaker_votes"].get)
                 
    # Verifica se c'è un pareggio nella votazione del Gufo
    if "owled_player" in game_state[chat_id] and len(
            game_state[chat_id]["tie_breaker_votes"]) == len(
                game_state[chat_id]["players"]) - 1:
        # Controlla se c'è un pareggio
        tie_votes = Counter(game_state[chat_id]["tie_breaker_votes"].values())
        if len(tie_votes) == 1 and list(tie_votes.values())[
                0] == 1:  # Tutti hanno ricevuto un voto
            # Pareggio: avvia una nuova votazione con gli altri giocatori
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Pareggio nella votazione del Gufo! Gli altri giocatori devono votare di nuovo."
            )
            game_state[chat_id]["tie_breaker_votes"] = {}  # Resetta i voti di spareggio
            await start_other_players_vote(update, context)
            return  # Esci dalla funzione per evitare di eliminare i giocatori

    # Resetta i voti di spareggio e lo stato tie_breaker
    game_state[chat_id]["tie_breaker_votes"] = {}
    del game_state[chat_id]["tie_breaker"]

    # Resetta i voti diurni
    game_state[chat_id]["day_votes"] = {}

    # Qui andrebbe implementata la logica per passare alla notte successiva
    # ... 
 
# Funzione per iniziare la votazione degli altri giocatori
async def start_other_players_vote(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    owled_player = game_state[chat_id]["owled_player"]
    tied_players = list(game_state[chat_id]["tie_breaker_votes"].keys())

    # Crea la tastiera con i giocatori per la votazione (escluso il "gufato" e i giocatori a pari merito)
    keyboard = []
    for player in game_state[chat_id]["players"]:
        if player != owled_player and player not in tied_players:
            keyboard.append([
                InlineKeyboardButton(player,
                                     callback_data=f"othervote_{player}")
            ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text=
        f"Votazione degli altri giocatori: scegliete chi eliminare tra {', '.join(tied_players)}.",
        reply_markup=reply_markup) 
 
# Funzione per terminare la votazione diurna (modificata con gestione dello spareggio)
async def end_day_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Determina il giocatore con più voti
    vote_counts = Counter(game_state[chat_id]["day_votes"].values())
    most_voted_players = [
        player for player, count in game_state[chat_id]["day_votes"].items()
        if count == max(vote_counts.values())
    ]

    if "owled_player" in game_state[chat_id]:
        # C'è un giocatore "gufato": gestisci lo spareggio a due
        owled_player = game_state[chat_id]["owled_player"]

        if len(most_voted_players) > 1:
            # Pareggio nella votazione iniziale: ripeti la votazione tra i giocatori a pari merito (escluso il "gufato")
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                f"Pareggio tra {', '.join(most_voted_players)}! Votate di nuovo (escluso {owled_player})."
            )
            game_state[chat_id]["tie_breaker"] = most_voted_players
            await start_tie_breaker_vote(update, context)
        else:
            # Spareggio tra il giocatore più votato e il "gufato"
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                f"Spareggio tra {most_voted_players[0]} e {owled_player}! Votate di nuovo."
            )
            game_state[chat_id]["tie_breaker"] = [
                most_voted_players[0], owled_player
            ]
            await start_tie_breaker_vote(update, context)
    else:
        # Elimina il giocatore con più voti
        victim = most_voted_players[0]  # Indentazione corretta
        await context.bot.send_message(chat_id=chat_id,
                                       text=f"{victim} è stato eliminato!")
        game_state[chat_id]["players"].remove(victim)
        del game_state[chat_id]["roles"][victim]

        # Resetta i voti diurni
        game_state[chat_id]["day_votes"] = {}

        # Controlla se la partita è finita
        await check_game_end(update, context)

        # Se la partita non è finita, passa alla notte successiva
    if game_state[chat_id]["phase"] != "end":
        await start_night(update, context)


# Funzione per iniziare la votazione di spareggio
async def start_tie_breaker_vote(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Crea la tastiera con i giocatori per lo spareggio (escluso il "gufato" se presente)
    keyboard = []
    for player in game_state[chat_id]["players"]:
        if player not in game_state[chat_id]["tie_breaker"] and (
                "owled_player" not in game_state[chat_id]
                or player != game_state[chat_id]["owled_player"]):
            keyboard.append([
                InlineKeyboardButton(player,
                                     callback_data=f"tiebreak_{player}")
            ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="Votazione di spareggio: scegliete chi eliminare.",
        reply_markup=reply_markup)


# Funzione per iniziare la notte (modificata)
async def start_night(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_state[chat_id]["phase"] = "night"
    game_state[chat_id]["night_count"] = game_state[chat_id].get(
        "night_count", 0) + 1  # Incrementa il contatore delle notti
    await context.bot.send_message(chat_id=chat_id,
                                   text="È notte! I lupi si svegliano...")

    # Attiva l'abilità del Mitomane alla fine della seconda notte
    if game_state[chat_id]["night_count"] == 2 and RUOLI[
            "Mitomane"] in game_state[chat_id]["roles"].values():
        await activate_copycat(update, context)


# Funzione per attivare l'abilità del Mitomane
async def activate_copycat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    copycat_player = [
        player for player, role in game_state[chat_id]["roles"].items()
        if role == RUOLI["Mitomane"]
    ][0]

    # Crea la tastiera con i giocatori per la scelta del Mitomane
    keyboard = []
    for player in game_state[chat_id]["players"]:
        if player != copycat_player:
            keyboard.append([
                InlineKeyboardButton(player, callback_data=f"copy_{player}")
            ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=copycat_player,  # Invia il messaggio in privato al Mitomane
        text=
        "Sei il Mitomane! Scegli un giocatore da copiare:",
        reply_markup=reply_markup)


# Funzione per controllare se la partita è finita
async def check_game_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    num_wolves = len([
        role for role in game_state[chat_id]["roles"].values()
        if role == RUOLI["Lupo"]
    ])
    num_humans = len(game_state[chat_id]["players"]) - num_wolves

    if num_wolves == 0:
        await context.bot.send_message(chat_id=chat_id,
                                       text="Gli umani hanno vinto!")
        game_state[chat_id]["phase"] = "end"
    elif num_wolves >= num_humans:
        await context.bot.send_message(chat_id=chat_id,
                                       text="I lupi hanno vinto!")
        game_state[chat_id]["phase"] = "end"
        
    # Se la partita è finita, genera il riepilogo
    if game_state[chat_id]["phase"] == "end":
        # Crea il messaggio di riepilogo con ruoli
        summary = "Riepilogo della partita:\n"
        for player, role in game_state[chat_id]["roles"].items():
            summary += f"{player}: {role['descrizione']}\n"

        await context.bot.send_message(chat_id=chat_id, text=summary)

        # Mostra il pulsante "Nuova partita"
        keyboard = [[KeyboardButton("Nuova partita")]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id,
                                       text="Vuoi iniziare una nuova partita?",
                                       reply_markup=reply_markup)

# Funzione per assegnare i ruoli (modificata)
def assign_roles(chat_id, context):
    players = game_state[chat_id]["players"].copy()  # Crea una copia della lista players
    roles = game_state[chat_id]["roles"].copy()  # Crea una copia della lista roles
    random.shuffle(players)
    random.shuffle(roles)

    # Assegna i ruoli ai giocatori
    game_state[chat_id]["roles"] = dict(zip(players, roles))

    # Invia un messaggio privato a ciascun giocatore con il suo ruolo
    for player, role in game_state[chat_id]["roles"].items():
        message = f"Il tuo ruolo è: **{role['descrizione']}**"
        if role["abilità"]:
            message += f"\nAbilità: {role['abilità']}"
        context.bot.send_message(chat_id=player,
                                   text=message,
                                   parse_mode="Markdown")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    # Aggiungi gli handler
    start_handler = CommandHandler('start', start)
    # Correzione: chiusura della stringa in filters.Regex
    newgame_handler = MessageHandler(filters.Regex("^(Nuova partita)$"), 
                                      newgame)  
    addplayer_handler = MessageHandler(filters.Regex("^(Aggiungi giocatore)$"),
                                        addplayer)
    start_role_selection_handler = MessageHandler(
        filters.Regex("^(Inizia selezione ruoli)$"), start_role_selection)

    # Aggiungi gli handler ai dispatcher
    application.add_handler(start_handler)
    application.add_handler(newgame_handler)
    application.add_handler(addplayer_handler)
    application.add_handler(start_role_selection_handler)

    # Aggiungi un handler per i messaggi di testo
    handle_message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND),
                                              handle_message)
    application.add_handler(handle_message_handler)

    # Aggiungi l'handler per i callback dei pulsanti
    application.add_handler(CallbackQueryHandler(handle_button_callback))

    # Aggiungi l'handler per il comando /endgame
    endgame_handler = CommandHandler('endgame', endgame)
    application.add_handler(endgame_handler)

    # Aggiungi l'handler per il comando /eliminati
    eliminati_handler = CommandHandler('eliminati', eliminati)
    application.add_handler(eliminati_handler)

    # Aggiungi l'handler per il comando /status
    status_handler = CommandHandler('status', status)
    application.add_handler(status_handler)

    # Avvia il bot
    application.run_polling()