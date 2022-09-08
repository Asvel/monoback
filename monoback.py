"""Generate aligned CJK fallback font for your favorite monospaced font."""

import argparse
import logging
from fontTools import ttLib

__version__ = '0.1.0'

logger = logging.getLogger(__name__)


def processFont(ttFont, ratio):
  if 'CFF ' in ttFont.reader.tables or 'CFF2' in ttFont.reader.tables:
    raise RuntimeError("OpenType/CFF font is not supported, view https://github.com/Asvel/monoback/issues/1 for detail.")

  halfWidth = round(ttFont['head'].unitsPerEm * ratio)
  fullWidth = round(ttFont['head'].unitsPerEm * ratio * 2)

  # give a new unique name
  # a font could fallback with different monospaced fonts, we need distinguish them
  name = ttFont['name']
  platformIDs = {n.platformID for n in name.names}
  names = []
  def addName(string, nameId):
    if nameId == 1 and len(string) > 31:
      # if family name longer than 31 characters, behaviors become weird under some render engines
      # preserve first three characters for sorting, and more suffixes for maximum distinction
      string = f'{string[:3]}..{string[-26:]}'
    if 1 in platformIDs: names.append(ttLib.tables._n_a_m_e.makeName(string, nameId, 1, 0, 0))
    if 3 in platformIDs: names.append(ttLib.tables._n_a_m_e.makeName(string, nameId, 3, 1, 1033))
    if 0 in platformIDs: names.append(ttLib.tables._n_a_m_e.makeName(string, nameId, 0, 3, 0))
  nameSuffix = f'Mono{fullWidth}'
  nameHyphen = '-' if '-' in name.getBestFamilyName() else ' '
  addName(f'{name.getBestFamilyName()}{nameHyphen}{nameSuffix}', 1)
  addName(f'{name.getBestSubFamilyName()}', 2)
  addName(f'{name.getDebugName(3)}{nameHyphen}{nameSuffix}', 3)
  addName(f'{name.getBestFullName()}{nameHyphen}{nameSuffix}', 4)
  addName(f'{name.getDebugName(5)};monoback {__version__}', 5)
  addName(f'{name.getDebugName(6)}-{nameSuffix}', 6)
  name.names = names + [n for n in name.names if n.nameID == 0 or 7 <= n.nameID <= 15]
  logger.info(name.getBestFamilyName())

  # change width of every glyph
  ttFont['hhea'].advanceWidthMax = fullWidth
  hmtx = ttFont['hmtx'].metrics
  for k, (width, lsb) in hmtx.items():
    destLsb = lsb + round((fullWidth - width) / 2)
    hmtx[k] = (fullWidth, destLsb)

  # indicate render engine to render in monospace mode, and align base on halfWidth
  ttFont['OS/2'].xAvgCharWidth = halfWidth
  ttFont['OS/2'].panose.bProportion = 9
  ttFont['post'].isFixedPitch = 1
  if 3 in platformIDs and ttFont['OS/2'].ulCodePageRange1 & (0b00111110 << 16) == 0:
    ttFont['OS/2'].ulCodePageRange1 |= (0b00111110 << 16)

  # discard pre-determined width since we expect render engine to decide glyph width as above
  ttFont.reader.tables.pop('hdmx', None)
  ttFont.reader.tables.pop('LTSH', None)
  ttFont['head'].flags &= ~(1 << 4)

  # kerning is not need since all glyph should display at fixed spacing
  ttFont.reader.tables.pop('kern', None)

  # warning for variable font
  if 'fvar' in ttFont.reader.tables:
    logger.warning("warning: the fallback font seem to be a variable font, this tool may not handle it properly, " +
      "and most code editors can't handle variation very well either, we recommend using a non-variable one.")

  return nameSuffix


def main():
  parser = argparse.ArgumentParser(description=__doc__, epilog=f'monoback {__version__} (https://github.com/Asvel/monoback)')
  parser.add_argument('monospaced', help="path of base monospaced font")
  parser.add_argument('fallback', help="path of source fallback font")
  parser.add_argument('output', nargs='?', help="path of patched fallback font")
  args = parser.parse_args()
  logging.basicConfig(level=logging.INFO, format='%(message)s')

  ttFont = ttLib.TTFont(args.monospaced, fontNumber=0)
  assert ttFont['hmtx'].metrics['i'][0] == ttFont['hmtx'].metrics['m'][0], f"{args.monospaced} is not monospaced."
  ratio = ttFont['hmtx'].metrics['i'][0] / ttFont['head'].unitsPerEm
  ttFont.close()

  nameSuffix = None
  if args.fallback.lower().endswith('.ttc'):
    ttFont = ttLib.ttCollection.TTCollection(args.fallback)
    logger.info("Generated font names:")
    for ttFont_ in ttFont.fonts:
      nameSuffix = processFont(ttFont_, ratio)
  else:
    ttFont = ttLib.TTFont(args.fallback)
    logger.info("Generated font name:")
    nameSuffix = processFont(ttFont, ratio)

  if args.output is None:
    rest, _, ext = args.fallback.rpartition('.')
    args.output = f'{rest}-{nameSuffix}.{ext}'
  ttFont.save(args.output)

  ttFont.close()


if __name__ == '__main__':
  main()
