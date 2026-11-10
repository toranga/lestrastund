# Lestrarstund

Lítið lestrarapp fyrir börn sem eru að læra að lesa á íslensku.

- **Stafir** – allir íslensku stafirnir með orði og mynd
- **Orð** – stutt, algeng orð til að æfa lestur
- **Dagbók** – stjörnur og lestrardagar síðustu vikuna
- 🔊 **Hlusta** – spilar tilbúnar hljóðskrár úr `audio/` ef þær eru til, annars íslenska rödd tækisins, eða rödd Google á netinu ef tækið hefur enga (t.d. Chrome á tölvu)
- 🎤 **Hlustaðu á mig** – athugar hvort barnið las rétt (Chrome)

Allt keyrir í vafranum í einni skrá (`index.html`). Framvinda vistast aðeins á tækinu.

## Betri íslensk rödd

`make_audio.py` býr til hljóðskrár fyrir alla stafi og orð einu sinni (Tiró, eða Guðrún með `edge-tts` ef Tiró svarar ekki):

```
pip install requests edge-tts
python make_audio.py
```

Settu svo `audio/` möppuna inn með `index.html`. Til að nota eigin upptöku fyrir orð, vistaðu hana undir sama nafni í `audio/`.

Opna appið: https://toranga.github.io/lestrastund/
