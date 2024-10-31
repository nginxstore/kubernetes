import requests
import time
from datetime import datetime
import argparse

class DowntimeTest:
    def __init__(self, service_url, test_duration=300, request_interval=0.1):
        self.service_url = service_url
        self.test_duration = test_duration
        self.request_interval = request_interval
        self.results = []
        self.is_running = False
        self.start_time = None
        
    def make_request(self):
        try:
            start_time = time.time()
            response = requests.get(self.service_url, timeout=1)
            end_time = time.time()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
        except requests.exceptions.RequestException:
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': 0,
                'success': False
            }

    def run_test(self):
        self.start_time = time.time()
        self.is_running = True
        
        while self.is_running and (time.time() - self.start_time) < self.test_duration:
            result = self.make_request()
            self.results.append(result)
            time.sleep(self.request_interval)
    
    def analyze_results(self):
        total_requests = len(self.results)
        failed_requests = sum(1 for r in self.results if not r['success'])
        success_rate = ((total_requests - failed_requests) / total_requests) * 100
        
        # 연속된 실패 기간 분석
        downtime_periods = []
        current_downtime = []
        
        for i, result in enumerate(self.results):
            if not result['success']:
                if not current_downtime:
                    current_downtime = [i]
                current_downtime.append(i)
            elif current_downtime:
                downtime_periods.append((
                    current_downtime[0],
                    current_downtime[-1],
                    (current_downtime[-1] - current_downtime[0]) * self.request_interval
                ))
                current_downtime = []

        return {
            'total_requests': total_requests,
            'failed_requests': failed_requests,
            'success_rate': success_rate,
            'downtime_periods': downtime_periods,
            'total_downtime': sum(d[2] for d in downtime_periods)
        }
    
    def save_results(self, filename):        
        analysis = self.analyze_results()
        with open(f'{filename}_analysis.txt', 'w') as f:
            f.write(f"Test Results for {self.service_url}\n")
            f.write(f"Duration: {self.test_duration} seconds\n")
            f.write(f"Request Interval: {self.request_interval} seconds\n\n")
            
            f.write(f"Total Requests: {analysis['total_requests']}\n")
            f.write(f"Failed Requests: {analysis['failed_requests']}\n")
            f.write(f"Success Rate: {analysis['success_rate']:.2f}%\n\n")
            
            f.write("Downtime Periods:\n")
            for start, end, duration in analysis['downtime_periods']:
                f.write(f"- {duration:.2f} seconds\n")
            f.write(f"Total Downtime: {analysis['total_downtime']:.2f} seconds\n\n")

def main():
    parser = argparse.ArgumentParser(description='Test deployment update strategy downtime')
    parser.add_argument('--url', required=True, help='Service URL to test')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    parser.add_argument('--interval', type=float, default=0.1, help='Request interval in seconds')
    parser.add_argument('--output', required=True, help='Output filename prefix')
    
    args = parser.parse_args()
    
    tester = DowntimeTest(args.url, args.duration, args.interval)
    tester.run_test()
    tester.save_results(args.output)

if __name__ == '__main__':
    main()