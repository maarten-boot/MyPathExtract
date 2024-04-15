import sys
import re

from typing import (
    Any,
    # Dict,
    Tuple,
    List,
    # Optional,
)


class MyPathExtract:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        data: Any,
        verbose: bool = False,  # be happy/chatty in your work
        fatal: bool = True,  # treat any path failure as fatal and raise a exception
    ) -> None:
        self.verbose = verbose
        self.data = data
        self.fatal = fatal

    def _validExtractorList(  # pylint: disable=too-many-branches
        self,
        pattern: str,
    ) -> Tuple[bool, Tuple[str, List[int]] | None]:  # pylint: disable=R0911
        if not (pattern.startswith("[") and pattern.endswith("]")):
            return False, None
        _s = "_validExtractorList::match: {pattern} to {r}"
        intList: List[int] = []

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
        first: str,
        rest: List[str],
        data: Any,
    ) -> Tuple[str, Any]:
        result: List[Any] = []
        n = 0
        for item in data:
            path = f"[{n}]"
            if len(rest) == 0:
                result.append((path, item))
            else:
                (r1, r2) = self._doFirstPathData(rest, item)
                result.append((path, (r1, r2)))
            n += 1
        return (first, result)

    def _doExtractListOne(
        self,
        hints: Tuple[str, List[int]],
        first: str,
        rest: List[str],
        data: Any,
    ) -> Tuple[str, Any]:
        what = hints[1][0]
        # lets see if the specified element exists
        try:
            r = data[what]
        except IndexError as e:
            if self.fatal:
                raise Exception(f"Fatal: data[{what}]) with data: {data}; {e}") from e
            r = None

        if len(rest) == 0:
            return (first, r)
        if r is None:
            return (first, r)

        return (first, self._doFirstPathData(rest, r))

    def _doExtractDictOne(
        self,
        first: str,
        rest: List[str],
        data: Any,
    ) -> Tuple[str, Any]:
        try:
            r = data.get(first)
        except Exception as e:
            if self.fatal:
                raise Exception(f"Fatal: get({first}) fails on data; {e}") from e
            if self.verbose:
                print(f"Err: get({first}) -> {e}; returning None", file=sys.stderr)

            return (first, None)

        if r is None:
            return (first, None)

        if len(rest) == 0:  # we have reached the end of the path list
            return (first, r)

        return (first, self._doFirstPathData(rest, r))

    def _doFirstPathData(
        self,
        pList: List[str],
        data: Any,
    ) -> Any:
        if self.verbose:
            print("_doFirstPathData", pList, data, file=sys.stderr)

        first = pList[0]
        rest = pList[1:]

        isList, hints = self._validExtractorList(first)
        if isList is not None and hints is not None:
            if hints[0] == "all":  # we process all items of the list
                return self._doExtractListAll(
                    first,
                    rest,
                    data,
                )
            if hints[0] == "one":
                return self._doExtractListOne(
                    hints,
                    first,
                    rest,
                    data,
                )

        return self._doExtractDictOne(
            first,
            rest,
            data,
        )

    def getPath(
        self,
        path: str,
    ) -> Any | None:
        if not path.startswith("/"):
            return None

        pList = path.split("/")
        d: Any = self.data
        result: Any = self._doFirstPathData(pList[1:], d)
        return result


if __name__ == "__main__":

    def main() -> None:
        verbose = True
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

        mpe = MyPathExtract(
            data=data,
            verbose=verbose,
            fatal=fatal,
        )

        pathList = [
            "/[*]/a/b/[*]",
            "/[*]/x",
            "/[*]/x/[*]/[*]",
            "/[*]/d",
            "/[*]/y/[*]/aa",
            "/[*]/a/b",
            "/[0]/a/b",
            "/[2]",
            "/[-1]",
            "/[-1]/y/[*]/aa",
        ]

        # all these paths should exist
        for path in pathList:
            r = mpe.getPath(path)
            print(r)

        if fatal is False:
            path = "/[*]/a/b/d"  # with the default (fatal: True),  we treat non existant path's as fatal error
            r = mpe.getPath(path)
            print(r)

    main()
