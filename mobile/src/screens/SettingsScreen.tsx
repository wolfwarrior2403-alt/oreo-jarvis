import React, {useEffect, useState} from 'react';
import {Alert, SafeAreaView, ScrollView, StyleSheet, Switch, Text, TextInput, TouchableOpacity, View} from 'react-native';
import Slider from '@react-native-community/slider';
import {useAuth} from '@/context/AuthContext';
import {
  getBackendUrl,
  getPorcupineAccessKey,
  getRetainRawAudio,
  getWakeWordSensitivity,
  setBackendUrl,
  setPorcupineAccessKey,
  setRetainRawAudio,
  setWakeWordSensitivity,
} from '@/services/storage';

/**
 * Settings (section 4.2 #4): wake word sensitivity, backend connection
 * (local IP for Option A, HTTPS cloud URL for Option B), and voice/data
 * retention controls. Retention here just toggles a client-side preference
 * the backend also reads via RETAIN_RAW_AUDIO — see backend/README.md;
 * this doesn't retroactively delete anything already stored server-side.
 */
export default function SettingsScreen() {
  const {logout} = useAuth();
  const [backendUrl, setBackendUrlState] = useState('');
  const [porcupineKey, setPorcupineKeyState] = useState('');
  const [sensitivity, setSensitivityState] = useState(0.5);
  const [retainAudio, setRetainAudioState] = useState(false);

  useEffect(() => {
    (async () => {
      setBackendUrlState((await getBackendUrl()) ?? '');
      setPorcupineKeyState((await getPorcupineAccessKey()) ?? '');
      setSensitivityState(await getWakeWordSensitivity());
      setRetainAudioState(await getRetainRawAudio());
    })();
  }, []);

  const saveBackendUrl = async (value: string) => {
    setBackendUrlState(value);
    await setBackendUrl(value.trim());
  };

  const savePorcupineKey = async (value: string) => {
    setPorcupineKeyState(value);
    await setPorcupineAccessKey(value.trim());
  };

  const saveSensitivity = async (value: number) => {
    setSensitivityState(value);
    await setWakeWordSensitivity(value);
  };

  const saveRetainAudio = async (value: boolean) => {
    setRetainAudioState(value);
    await setRetainRawAudio(value);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.section}>Backend connection</Text>
        <Text style={styles.label}>Backend URL (local IP or cloud URL)</Text>
        <TextInput
          style={styles.input}
          value={backendUrl}
          onChangeText={saveBackendUrl}
          placeholder="http://192.168.1.20:8000 or https://oreo.example.com"
          placeholderTextColor="#6B6B7B"
          autoCapitalize="none"
          autoCorrect={false}
        />

        <Text style={styles.section}>Wake word</Text>
        <Text style={styles.label}>Picovoice AccessKey (required for "Oreo" detection)</Text>
        <TextInput
          style={styles.input}
          value={porcupineKey}
          onChangeText={savePorcupineKey}
          placeholder="Get one at console.picovoice.ai"
          placeholderTextColor="#6B6B7B"
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry
        />
        <Text style={styles.label}>Sensitivity: {sensitivity.toFixed(2)}</Text>
        <Slider
          style={styles.slider}
          minimumValue={0}
          maximumValue={1}
          step={0.05}
          value={sensitivity}
          onValueChange={saveSensitivity}
          minimumTrackTintColor="#6C5CE7"
        />

        <Text style={styles.section}>Data retention</Text>
        <View style={styles.row}>
          <Text style={styles.label}>Keep raw audio after transcription</Text>
          <Switch value={retainAudio} onValueChange={saveRetainAudio} />
        </View>
        <Text style={styles.hint}>
          Off by default (section 6: data minimization). The backend must also have RETAIN_RAW_AUDIO enabled for
          this to take effect server-side.
        </Text>

        <TouchableOpacity
          style={styles.logoutButton}
          onPress={() =>
            Alert.alert('Unpair device', 'This clears stored credentials on this device.', [
              {text: 'Cancel', style: 'cancel'},
              {text: 'Unpair', style: 'destructive', onPress: logout},
            ])
          }>
          <Text style={styles.logoutText}>Unpair this device</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#0F0E17'},
  content: {padding: 20, gap: 8},
  section: {color: '#6C5CE7', fontSize: 13, fontWeight: '700', textTransform: 'uppercase', marginTop: 20},
  label: {color: '#A7A9BE', fontSize: 14, marginTop: 8},
  hint: {color: '#6B6B7B', fontSize: 12, marginTop: 4},
  input: {
    backgroundColor: '#1F1D33',
    color: '#FFFFFE',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginTop: 4,
  },
  slider: {marginTop: 4},
  row: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8},
  logoutButton: {marginTop: 32, paddingVertical: 14, borderRadius: 12, backgroundColor: '#3A1F2E', alignItems: 'center'},
  logoutText: {color: '#FF6B6B', fontWeight: '600'},
});
