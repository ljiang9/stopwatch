"""stopwatch: 终端秒表, 支持计圈和倒计时。纯标准库。"""
import argparse
import sys
import threading
import time


def fmt(seconds):
    """格式化为 mm:ss.cc (分:秒.厘秒)。负数按 0 处理。"""
    if seconds < 0:
        seconds = 0
    total_cs = int(round(seconds * 100))
    mm, rest = divmod(total_cs, 6000)
    ss, cs = divmod(rest, 100)
    return "%02d:%02d.%02d" % (mm, ss, cs)


class Stopwatch:
    """可注入时钟的秒表, 便于测试。"""

    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self._start = None
        self._elapsed = 0.0
        self.laps = []

    def start(self):
        if self._start is None:
            self._start = self._clock()

    def lap(self):
        """计一圈, 返回本圈时长。未启动返回 None。"""
        if self._start is None:
            return None
        now = self._clock()
        lap_time = now - self._start
        self.laps.append(lap_time)
        self._elapsed += lap_time
        self._start = now
        return lap_time

    def stop(self):
        if self._start is not None:
            self._elapsed += self._clock() - self._start
            self._start = None
        return self._elapsed

    def total(self):
        t = self._elapsed
        if self._start is not None:
            t += self._clock() - self._start
        return t

    def best(self):
        return min(self.laps) if self.laps else None


def run_stopwatch():
    if not sys.stdin.isatty():
        print("error: 交互模式需要终端, 请在终端里运行。", file=sys.stderr)
        return 2
    sw = Stopwatch()
    sw.start()
    stop_flag = threading.Event()

    def ticker():
        while not stop_flag.is_set():
            sys.stdout.write("\r当前 %s  (回车=计圈, q=退出)" % fmt(sw.total()))
            sys.stdout.flush()
            time.sleep(0.05)
        sys.stdout.write("\r" + " " * 50 + "\r")

    th = threading.Thread(target=ticker, daemon=True)
    th.start()
    try:
        for line in sys.stdin:
            cmd = line.strip().lower()
            if cmd in ("q", "quit", "exit"):
                break
            lap = sw.lap()
            if lap is not None:
                best = sw.best()
                print("\n第 %d 圈 %s | 上一圈 %s | 最快 %s | 总计 %s" % (
                    len(sw.laps), fmt(lap), fmt(lap),
                    fmt(best), fmt(sw.total())))
    except KeyboardInterrupt:
        pass
    finally:
        stop_flag.set()
        th.join()
    total = sw.stop()
    print("\n停止。总计 %s, 共 %d 圈。" % (fmt(total), len(sw.laps)))
    if sw.laps:
        print("最快一圈: %s" % fmt(sw.best()))
    return 0


def run_countdown(seconds, beep=True):
    if seconds <= 0:
        print("error: 倒计时秒数必须大于 0。", file=sys.stderr)
        return 2
    end = time.monotonic() + seconds
    try:
        while True:
            left = end - time.monotonic()
            if left <= 0:
                break
            sys.stdout.write("\r剩余 %s" % fmt(left))
            sys.stdout.flush()
            time.sleep(min(0.05, left))
    except KeyboardInterrupt:
        print("\n已取消。")
        return 0
    sys.stdout.write("\r" + " " * 20 + "\r")
    print("时间到!")
    if beep:
        sys.stdout.write("\a\a\a")
        sys.stdout.flush()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="stopwatch", description="终端秒表: 计圈 / 倒计时")
    ap.add_argument("--countdown", type=float, metavar="秒",
                    help="倒计时模式, 秒数 (支持小数)")
    args = ap.parse_args(argv)
    if args.countdown is not None:
        return run_countdown(args.countdown)
    return run_stopwatch()


if __name__ == "__main__":
    raise SystemExit(main())
