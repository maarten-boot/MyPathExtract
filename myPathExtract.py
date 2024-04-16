import sys
import re

from typing import (
    Any,
    Tuple,
    List,
)


class PathExtractor:
    def __init__(
        self,
        verbose: bool = False,
        fatal: bool = True,
    ) -> None:
        self.data: Any = None
        self.verbose = verbose
        self.fatal = fatal
        self.currentPath: list[str] = []
        self.resultList: List[Tuple[str, Any]] = []  # the result as list of tuple: (path, data)

    def setData(self, data: Any) -> None:
        self.data = data

    def getCurrentPath(self) -> str:
        return "/" + "/".join(self.currentPath)

    def _validExtractorList(  # pylint: disable=too-many-branches
        self,
        pattern: str,
    ) -> Tuple[bool, Tuple[str, List[int]]]:  # pylint: disable=R0911
        _s = "_validExtractorList::match: {pattern} to {r}"
        intList: List[int] = []

        if not (pattern.startswith("[") and pattern.endswith("]")):
            r = False, ("", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        if pattern in ["[*]"]:
            r = True, ("all", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        m = re.match(r"\[([+-]?\d+)\]", pattern)
        if m:
            one = int(m[1])
            intList = [one]
            r = True, ("one", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        m = re.match(r"\[:(\d+)\]", pattern)
        if m:
            end = int(m[1])
            intList = [end]
            r = True, ("range_toX", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        m = re.match(r"\[(\d+):\]", pattern)
        if m:
            start = int(m[1])
            intList = [start]
            r = True, ("range_fromX", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        m = re.match(r"\[(\d+):(\d+)\]", pattern)
        if m:
            start = int(m[1])
            end = int(m[2])
            intList = [start, end]
            r = True, ("range", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        m = re.match(r"\[(\d+(\s*,\s*\d+)*)\]", pattern)
        if m:
            strWithComma = m[1]
            strList = strWithComma.split(",")
            for s in strList:
                intList.append(int(s.strip()))
            r = True, ("list", intList)
            if self.verbose:
                print(_s.format(pattern=pattern, r=r), file=sys.stderr)
            return r

        if self.fatal:
            raise Exception(f"Fatal: unsupported List processing pattern: {pattern}")

        assert False

    def _doExtractListAll(
        self,
        rest: List[str],
        data: Any,
    ) -> None:
        n = 0
        for item in data:
            path = f"[{n}]"
            self.currentPath.append(path)
            if len(rest) > 0:
                self._doFirstPathData(rest, item)
            else:
                self.resultList.append((self.getCurrentPath(), item))
            n += 1
            self.currentPath.pop()

    def _doExtractListOne(
        self,
        hints: Tuple[str, List[int]],
        rest: List[str],
        data: Any,
    ) -> None:
        what = hints[1][0]
        # lets see if the specified element exists
        try:
            result = data[what]
        except IndexError as e:
            if self.fatal:
                raise Exception(f"Fatal: data[{what}]) with data: {data}; {e}") from e
            result = None

        if result is None:
            self.resultList.append((self.getCurrentPath(), result))
            return

        if len(rest) == 0:
            return

        self._doFirstPathData(rest, result)

    def _doExtractDictOne(
        self,
        first: str,
        rest: List[str],
        data: Any,
    ) -> None:
        if self.verbose:
            print("_doExtractDictOne", first, rest, data, file=sys.stderr)

        try:
            result = data[first]
        except KeyError as e:
            if self.verbose:
                print(first, rest, data, e, file=sys.stderr)
            return
        except IndexError as e:
            if self.verbose:
                print(first, rest, data, e, file=sys.stderr)
            return
        except TypeError as e:  # we are indexing a list with a string
            if self.verbose:
                print(first, rest, data, e, file=sys.stderr)
            return

        if len(rest) == 0:  # we have reached the end of the path list, so book the result and return
            self.resultList.append((self.getCurrentPath(), result))
            return

        # otherwise continue looking along the path for data
        self._doFirstPathData(rest, result)

    def _doFirstPathData(
        self,
        pList: List[str],
        data: Any,
    ) -> None:
        first = pList[0]
        rest = pList[1:]

        if self.verbose:
            print("_doFirstPathData", pList, first, rest, data, file=sys.stderr)

        isList, hints = self._validExtractorList(first)  # should we extract a list [?]

        if isList is True:
            if hints[0] == "all":  # we process all items of the list
                self._doExtractListAll(
                    rest,
                    data,
                )
                return

            if hints[0] == "one":
                self.currentPath.append(first)
                self._doExtractListOne(
                    hints,
                    rest,
                    data,
                )
                self.currentPath.pop()
                return

        self.currentPath.append(first)
        self._doExtractDictOne(
            first,
            rest,
            data,
        )
        self.currentPath.pop()

    def extractAllWithPath(self, path: str) -> List[Tuple[str, Any]]:
        if not path.startswith("/"):
            if self.fatal:
                raise Exception(f"Fatal: missing start '/' on path {path}")
            return []

        if self.verbose:
            print(f"extractAllWithPath({path})", file=sys.stderr)

        # prepare
        self.currentPath = []
        self.resultList = []
        pList = path.split("/")[1:]  # the current request path as list at this level
        data: Any = self.data  # the data at this level

        self._doFirstPathData(
            pList,
            data,
        )

        # process the result for data-path and data
        return self.resultList


if __name__ == "__main__":

    def main() -> None:
        verbose = True
        verbose = False
        fatal = True

        data = [
            {
                "a": {
                    "b": [
                        "aa",
                        3,
                        "777",
                    ],
                }
            },
            {"d": "hhh"},
            {
                "x": [
                    ["aa"],
                    [3],
                    ["777"],
                ]
            },
            {
                "y": [
                    {"aa": "some aa"},
                    {"bb": "some bb"},
                ]
            },
        ]

        pe = PathExtractor(verbose=verbose, fatal=fatal)
        pe.setData(data)

        pathList = [
            "/[*]/a/b/[*]",
            "/[*]/x",
            "/[*]/x/[*]/[*]",
            "/[*]/d",
            "/[*]/y/[*]/aa",
            "/[*]/y/[*]",
            "/[*]/a/b",
            "/[0]/a/b",
            "/[2]",
            "/[-1]",
            "/[-1]/y/[*]/aa",
            "/[*]/a/b/d",
            "/a/b/d",
        ]

        # all these paths should exist
        for path in pathList:
            r = pe.extractAllWithPath(path)
            print(f"with path: {path}; we get result: {r}")
            # sys.exit(0)

    main()
