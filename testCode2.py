import serial
import time
import keyboard
import threading
import time
import keyboard

class PumpTimer(threading.Thread):
    def __init__(self, run_time):
        super().__init__()
        self.run_time = run_time
        self.running = True
        self.paused = False

    def run(self):
        start_time = time.time()
        while self.running:
            if not self.paused:
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time >= self.run_time:
                    print("Pump time is up!")
                    self.running = False
                    print(f"Elapsed time: {elapsed_time:.2f} seconds")
                    break
            else:  # If paused, don't update the elapsed time
                start_time = time.time() - elapsed_time  # Reset the start time to account for paused time
                print(f"Pause time: {elapsed_time:.2f}")
               
            time.sleep(1) 


    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False




class TestSerialCommunication:
    def __init__(self, port):
        self.serial_port = port
        self.ser = None

### SERIAL COMMUNICATION ###

    def connect(self):
        try:
            self.ser = serial.Serial(self.serial_port, baudrate=9600, timeout=0.1)
            print("Serial connection established.")
        except serial.SerialException as e:
            print("Error:", e)

    def send_receive(self, command):
        if not self.ser:
            print("Serial port not connected.")
            return
        try:
            self.ser.write(command.encode('ASCII'))
            response = self.ser.read_until(b'\x0D')
            print("Sent command:", command)
            print("Received response:", response)
        except serial.SerialException as e:
            print("Error:", e)
            
    def disconnect(self):
        if self.ser:
            self.ser.close()
            print("Serial connection closed.")
    
            
### Operational Modes and Settings ###

    def setPumpRPM(self, pumpNumber, direction, speed):
        self.send_receive(f"{pumpNumber}L\x0D")  # Set the flow rate
        self.send_receive(f"{pumpNumber}{direction}\x0D")  # Set direction
        self.send_receive(f"{pumpNumber}S{self._discrete3(speed)}\x0D")  # Set speed
    
    def setTubeDiameter(self, pumpNumber, width):
        self.send_receive(f"{pumpNumber}+{self._discrete2(width)}\x0D") #Set tube diameter
        
    
    def setFlowRate(self, pumpNumber, direction, volume):
        self.send_receive(f"{pumpNumber}M\x0D")  # Set the flow rate mode
        self.send_receive(f"{pumpNumber}{direction}\x0D")  # Set direction
        self.send_receive(f"{pumpNumber}f{self._volume2(volume)}\x0D") # Set mL/min rate
    """"
    def resetCalibration(self):
        self.send_receive("000000\x0D") # Sets pump to default settings
    """
        
### ACTUATION CONTROLS ###

    def allPumpsOn(self):
        #self.send_receive("1H\x0D")
        #self.send_receive("2H\x0D")
        self.send_receive("3H\x0D")
        self.send_receive("4H\x0D")
        
    def allPumpsOff(self):
        #self.send_receive("1I\x0D")
        #self.send_receive("2I\x0D")
        self.send_receive("3I\x0D")
        self.send_receive("4I\x0D")

### CONVERSION METHODS ###

    def _time1(self, number, units='s'):
        """Convert number to 'time type 1'.

        1-8 digits, 0 to 35964000 in units of 0.1s
        (0 to 999 hr)
        """
        number = 10 * number  # 0.1s
        if units == 'm':
            number = 60 * number
        if units == 'h':
            number = 60 * number
        return str(min(number, 35964000)).replace('.', '')

    def _time2(self, number, units='s'):
        """Convert number to 'time type 2'.

        8 digits, 0 to 35964000 in units of 0.1s, left-padded with zeroes
        (0 to 999 hr)
        """
        number = 10 * number  # 0.1s
        if units == 'm':
            number = 60 * number
        if units == 'h':
            number = 60 * number
        return str(min(number, 35964000)).replace('.', '').zfill(8)

    def _volume2(self, number):
        # convert number to "volume type 2"
        number = '%.3e' % abs(number)
        number = number[0] + number[2:5] + number[-3] + number[-1]
        print(str(number))
        return str(number)
        
    def _volume1(self, number):
        # convert number to "volume type 1"
        number = '%.3e' % abs(number)
        number = number[0] + number[2:5] + 'E' + number[-3] + number[-1]
        return number

    def _discrete2(self, number):
        # convert float to "discrete type 2"
        number = int(number * 100)
        s = str(number)
        return str(number).zfill(4)

    def _discrete3(self, number):
        """Convert number to 'discrete type 3'.

        6 digits, 0 to 999999, left-padded with zeroes
        """
        number = int(number * 100)
        s = str(number)
        return str(number).zfill(6)


def main():

    serial_port = 'COM7'  # Replace with your pump's serial port
    test_comm = TestSerialCommunication(serial_port)
    test_comm.connect() 
        
    pump_timer = PumpTimer(30)
    print("Press 'q' to pause the timer.")
    pump_timer.start()
    test_comm.setTubeDiameter("3", 0.38) #Setting channel 3 pump to a diameter of 0.013 mL
    test_comm.setTubeDiameter("4", 0.38) #Setting channel 3 pump to a diameter of 0.013 mL
    test_comm.setFlowRate("3", "J", 0.35) #Setting channel 3 to flow rate mode - RPM speed dependent on Tube Diameter
    test_comm.setFlowRate("4", "J", 0.3) #Setting channel 3 to flow rate mode - RPM speed dependent on Tube Diameter
    test_comm.allPumpsOn()
    
    while pump_timer.running:
        if keyboard.is_pressed('q'):  # Check for 'q' key
            test_comm.allPumpsOff()
            pump_timer.pause()
            print("Timer paused.")
        elif keyboard.is_pressed('r'):
            test_comm.allPumpsOn()
            pump_timer.resume()
            print("Timer resumed.")
    
    pump_timer.join()
    test_comm.allPumpsOff()
        
    """
    test_comm.setPumpRPM("4", "J", 10)
    """
    """    test_comm.allPumpsOn()
    time.sleep(2)
    test_comm.allPumpsOff()
    test_comm.setPumpRPM("4", "J", 50)
    test_comm.allPumpsOn()q
    time.sleep(4)
    test_comm.allPumpsOff()
    test_comm.setPumpRPM("4", "J", 100)
    test_comm.allPumpsOn()
    time.sleep(6)   
    test_comm.allPumpsOff()
    """

    
if __name__ == "__main__":
    main()
