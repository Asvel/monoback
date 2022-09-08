# monoback

Generate aligned CJK fallback font for your favorite monospaced font.

[中文介绍](README-CN.md)


## Installation

Install from PyPI (requires Python 3.7+):
```
pip install monoback
```

Or download standalone executable from [release page](https://github.com/Asvel/monoback/releases/latest). (Windows only)


## Usage

```
monoback <monospaced-font-file> <fallback-font-file> [<output-file>]
```

Then install the generated font and configure it as fallback font in your editor settings, examples:
* In VSCode, set `Editor: Font Family` to string `'main monospaced font name', 'generated font name'`.
* In JetBrains products, set `Editor > Font > Typography Settings > Fallback font` to generated font.


## License

monoback is licensed under the [MIT license](LICENSE.txt).
