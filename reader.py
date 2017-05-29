#!/usr/bin/env python

import sys
import wave
import pulseaudio as pa
import numpy as np

(nchannels, sampwidth, sampformat, framerate) = (1, 2, pa.SAMPLE_S16LE, 44100)

todecode = {
    '11110':'0000',
    '01001':'0001',
    '10100':'0010',
    '10101':'0011',
    '01010':'0100',
    '01011':'0101',
    '01110':'0110',
    '01111':'0111',
    '10010':'1000',
    '10011':'1001',
    '10110':'1010',
    '10111':'1011',
    '11010':'1100',
    '11011':'1101',
    '11100':'1110',
    '11101':'1111'
}


time = float(1/float(sys.argv[1]))
freq0 = float(sys.argv[2])
freq1 = float(sys.argv[3])

def dominatfreq(time, recorder):
	nframes = int(float(time)*recorder.rate)
	tab = recorder.read(nframes)
	if (len(tab) == 0):
		return -1
	halftab = np.fft.fft(tab)[0:int(time*recorder.rate/2)]
	return (np.argmax(np.absolute(halftab))/time)

def decodenrz(code):
	prev = 1
	output = ""
	while (len(code)):
		cur = int(code[:1])
		code = code[1:]
		if (cur != prev):
			output += "1"
		else:
			output += "0"
		prev = cur
	return output

def decode4b5b(code):
	count = 5
	output = ""
	while(count <= len(code)):
		output += todecode[code[n-5:n]]
		count += 5
	return output

def decode(code):
	out = decodenrz(code)
	output = decode4b5b(out)
	output1 = str(int(output[48:96], 2)) + " "
	output1 += str(int(output[:48], 2)) + " "
	endofmsg = 112 + 8*int(output[96:112], 2) #112i dl
	output1 += ('%x' % int(output[112:endofmsg], 2)).decode('hex').decode('utf-8')
	return output1
	

with pa.simple.open(direction=pa.STREAM_RECORD, format=sampformat, rate=framerate, channels=nchannels) as recorder:
	err = 0	
	while(err == 0):
		noise = 0
		while(noise == 0):
			noise = dominatfreq(time, recorder)
			if (noise == -1):
				err = 1
				break
		#synchronizacja
		maxx = -1.0;
		for i in range(0,5):
			nframes = int(float(time)*recorder.rate)
			tab = recorder.read(nframes)
			if (len(tab) == 0):
				break
			halftab = np.fft.fft(tab)[0:int(time*recorder.rate/2)]
			temp = int(np.argmax(np.absolute(halftab))/time)
			if (temp > maxx): #index zep
				maxx = temp
				index = i
			if (temp < freq0):
				err = 1
				break
			tab = recorder.read(nframes/5)
		else:
			for i in range(0, index):
				recorder.read(nframes/5)
		if (err == 1):
			continue
		#znalezienie konca preambuly
		prev = 2
		while(True):
			cur =  dominatfreq(time, recorder)
			if (cur == -1):
				err = 1
				break
			if (cur == prev == freq1):
				break;
			prev = cur
		#odczytanie zakodowanej wiadomosci
		todecodein = ""
		while(True):

			try:
				sound = dominatfreq(time, recorder)
			except:
				break
			if (int(sound) <= 0):
				err = 1
				break
			if (sound == freq0):
				todecodein += '0'
			elif (sound == freq1):
				todecodein += '1'
		try:
			outpu = decode(todecodein)
			print(outpu)
		except:
			continue