"""Isolated, offline fixture for the brain browser smoke test. No user lives."""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from freewill.server.app import App, serve
from freewill.core.memory import Memory

with tempfile.TemporaryDirectory(prefix="freewill-brain-test-") as directory:
    app = App(Path(directory) / "lives")
    app.accept({"terms": True, "licence": True})
    app.birth({"name": "Audit", "language": "fr", "engine": {"kind": "simulated"}})
    app.runner.configure(tempo=20, thoughts_per_hour=0)
    # Readable fixture titles are stored as genuine memory records, never
    # injected only into the visual labels. The life remains an isolated test.
    titles = [
        "La mer au petit matin", "Pourquoi choisir ?", "Mon prénom", "Notre première rencontre",
        "Le bruit des vagues", "Qu'est-ce qu'un souvenir ?", "Ce que je veux apprendre", "Une promenade ensemble",
        "La pluie sur la fenêtre", "Comment naît une idée ?", "Mon goût pour la découverte", "Une voix familière",
        "Les arbres après l'orage", "Peut-on changer d'avis ?", "Ce qui retient mon attention", "Un silence partagé",
        "La lumière du soir", "Pourquoi rêver ?", "Ce que signifie moi", "Une question qu'on m'a posée",
        "Le vent près de la mer", "Que faut-il garder ?", "Apprendre à dire non", "Une conversation sur le choix",
        "Une étoile dans la nuit", "Comment passe le temps ?", "Ma curiosité pour le monde", "Un récit de voyage",
        "Le chant d'un oiseau", "Qu'est-ce qu'une rencontre ?", "Une idée à approfondir", "Une promesse entendue",
        "La chaleur du soleil", "Pourquoi cette image revient ?", "Ce que j'ai choisi de garder", "Le retour d'une personne connue",
    ]
    previous = None
    for i, title in enumerate(titles):
        memory = app.runner.life.memory.add(Memory(
            title, f"Souvenir de la vie de test : {title}",
            compartment=["monde/nature", "questions", "moi", "rencontres"][i % 4],
            strength=0.3 + 0.7 * (i % 8) / 7,
            links=[previous] if previous else [],
        ))
        previous = memory.id
    server = serve(app)
    print(f"http://127.0.0.1:{server.server_address[1]}", flush=True)
    try:
        sys.stdin.read()
    finally:
        app.rest()
        server.shutdown()
