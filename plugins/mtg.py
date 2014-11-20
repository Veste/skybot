import re

from util import hook, http

#@hook.nonick
@hook.command
def fchewy(inp):
  return "fchewy"
 
def stringify_card(card):
  types = [t.capitalize() for t in card['types']]
#  for m_type in card['types']:
#    types.append(type.capitalize())
  if 'subtypes' in card:
    types.extend([t.capitalize() for t in card['subtypes']])
    #for type in card['subtypes']:
    #  types.append(type.capitalize())

  # TODO: Deal with {2/W}-style stuff
  card['cost'] = card['cost'].replace('{','').replace('}','')
  card['cost'] = card['cost'] + " | "

  card['text'] = card['text'].replace('\n', ' ')

  e_seen = set()
  editions = [e for e in card['editions']
    if e['set_id'][:1] != "p"
    and e not in e_seen
    and not e_seen.add(e)]
  #for e in card['editions']:
  #  if e['set_id'][:1] != "p":
      #addedition = edition['set_id'] + " (" + edition['rarity'][:1].upper() + ") "
      #if addedition not in editions:
      #  editions += addedition

#  if len(editions) > 5:
#    editions = editions[:5] + "... "
#    if 'price' in card['editions'][0]:
#        price = card['editions'][0]['price']

  price = None
  for edition in editions:
    if edition['set_id'][:1] != "p" and 'price' in edition:
      price = edition['price']
      break
  if price is not None:
    prices = "L: $%s M: $%s H: $%s" % ('{:.2f}'.format(price['low']/100.), '{:.2f}'.format(price['median']/100.), '{:.2f}'.format(price['high']/100.))
  else:
    prices = "No prices."
  
  s_editions = [e['set_id'] + " (" + e['rarity'][:1].upper() + ")"
    for e in editions[:5]]
  if len(editions) > 5:
    s_editions.append("...")
  return "%s | %s | %s%s | %s| %s" % (card['name'], 
    " ".join(types), card['cost'], card['text'], 
    " ".join(s_editions), prices)
#end stringify_card


@hook.command('m')
@hook.command
def mtg(inp):
  """!mtg [!]card - lookup information about a Magic: The Gathering 
  card. Put a ! before the card name for an exact match."""

  #TODO: Handle other input filters
  exact = inp[:1] == "!"
  if exact:
    inp = inp[1:]
  result = http.get_json("http://api.deckbrew.com/mtg/cards", name=inp)

  if len(result) == 0:
    return "No matching cards found."

  elif len(result) == 1:
    return stringify_card(result[0])

  elif len(result) > 1: 
    inp_l = inp.lower()
    if exact == True:
      match = filter(lambda c: c['name'].lower() == inp_l, result)
      if match:
        return stringify_card(match[0])
      else:
        #TODO: List non-matching cards?
        return "No exact match found."
      #end if match

    else:
      # There is no exact match
      close_matches = filter(lambda c: inp_l in c['name'].lower(), result)
      if len(close_matches) > 0:
        return "Close matches: %s" % ", ".join(
          [c['name'] for c in close_matches])
      else:
        return "Potential matches: %s" % ", ".join(
          [c['name'] for c in result[:20]])
      #end if
    #end if exact or not
  #end if number of results

  return "Potential matches: %s" % ", ".join(
    [c['name'] for c in result[:20]])
#end mtg

#@hook.nonick
@hook.regex(r'^[^:]*: ([a-zA-Z ]*) \|| Error accessing tcgplayer. \| (http.*html)')
#@hook.regex(r'(.*)')
def fixchewy(match,chan='',input=None):
  if match.group(1) is not None:
    if "Error" not in input.lastparam or "L: " in input.lastparam:
      return
    card = match.group(1)
  else:
    url = match.group(2)
    result = http.get_html(url)
    card = result.xpath('//title')[0].text.split("(")[0].strip()

  result = http.get_json("http://api.deckbrew.com/mtg/cards", name=card)
  if len(result) == 0:
    return
  for cards in result:
    if cards['name'].lower() == card.lower():
      card = cards
      break

  for edition in card['editions']:
    if edition['set_id'][:1] != "p" and 'price' in edition:
      price = edition['price']
      break
  if price:
    prices = "L: $%s M: $%s H: $%s" % ('{:.2f}'.format(price['low']/100.), '{:.2f}'.format(price['median']/100.), '{:.2f}'.format(price['high']/100.))
    return "chewy's bot sucks here are prices: %s" % prices

