import React, {useState} from 'react';
import {Alert, SafeAreaView, StyleSheet, Text, TextInput, TouchableOpacity} from 'react-native';
import {pairDevice} from '@/api/auth';
import {setBackendUrl} from '@/services/storage';
import {useAuth} from '@/context/AuthContext';

/**
 * First-run device pairing (section 3.1 "/auth/pair", section 4.4). Not one
 * of the doc's four core screens, but a required entry point before Home/
 * History/Settings mean anything — there's no session to show without it.
 */
export default function PairingScreen() {
  const {refresh} = useAuth();
  const [backendUrl, setBackendUrlInput] = useState('http://192.168.1.20:8000');
  const [pairingCode, setPairingCode] = useState('');
  const [deviceName, setDeviceName] = useState('My Phone');
  const [busy, setBusy] = useState(false);

  const handlePair = async () => {
    if (!backendUrl || !pairingCode) {
      Alert.alert('Oreo', 'Backend URL and pairing code are both required.');
      return;
    }
    setBusy(true);
    try {
      await setBackendUrl(backendUrl.trim());
      await pairDevice(backendUrl.trim(), pairingCode.trim(), deviceName.trim() || 'My Phone');
      await refresh();
    } catch (err) {
      Alert.alert('Oreo', 'Pairing failed. Check the backend URL and pairing code (DEVICE_PAIRING_CODE on the backend).');
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Pair with Oreo</Text>
      <Text style={styles.hint}>
        Get the pairing code and backend URL from whoever set up your Oreo backend (see backend/README.md).
      </Text>

      <TextInput
        style={styles.input}
        value={backendUrl}
        onChangeText={setBackendUrlInput}
        placeholder="Backend URL"
        placeholderTextColor="#6B6B7B"
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        value={pairingCode}
        onChangeText={setPairingCode}
        placeholder="Pairing code"
        placeholderTextColor="#6B6B7B"
        autoCapitalize="none"
        secureTextEntry
      />
      <TextInput
        style={styles.input}
        value={deviceName}
        onChangeText={setDeviceName}
        placeholder="Device name"
        placeholderTextColor="#6B6B7B"
      />

      <TouchableOpacity style={styles.button} onPress={handlePair} disabled={busy}>
        <Text style={styles.buttonText}>{busy ? 'Pairing…' : 'Pair device'}</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#0F0E17', padding: 24, justifyContent: 'center', gap: 12},
  title: {color: '#FFFFFE', fontSize: 28, fontWeight: '700', textAlign: 'center'},
  hint: {color: '#A7A9BE', fontSize: 14, textAlign: 'center', marginBottom: 12},
  input: {
    backgroundColor: '#1F1D33',
    color: '#FFFFFE',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  button: {backgroundColor: '#6C5CE7', borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 8},
  buttonText: {color: '#FFFFFE', fontWeight: '700', fontSize: 16},
});
