import React, {useState} from 'react';
import {ActivityIndicator, SafeAreaView, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import type {NativeStackScreenProps} from '@react-navigation/native-stack';
import {decideAction} from '@/api/actions';
import type {RootStackParamList} from '@/navigation/AppNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Confirmation'>;

/**
 * Confirmation dialog (section 4.2 #2). This is the mobile half of the
 * confirmation gate described in the architecture doc's section 6: nothing
 * proposed by the reasoning agent executes until the user taps Approve
 * here, which calls POST /execute/action. Cancel calls the same endpoint
 * with approve=false, which the backend records as `rejected` and never
 * runs.
 */
export default function ConfirmationScreen({route, navigation}: Props) {
  const {actionId, summary} = route.params;
  const [busy, setBusy] = useState(false);
  const [outcome, setOutcome] = useState<'approved' | 'rejected' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const respond = async (approve: boolean) => {
    setBusy(true);
    setError(null);
    try {
      await decideAction(actionId, approve);
      setOutcome(approve ? 'approved' : 'rejected');
      setTimeout(() => navigation.goBack(), 900);
    } catch (err) {
      setError('Could not reach the backend to confirm this action.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.heading}>Oreo wants to:</Text>
        <Text style={styles.summary}>{summary}</Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        {outcome ? (
          <Text style={styles.outcome}>{outcome === 'approved' ? 'Approved ✓' : 'Cancelled'}</Text>
        ) : busy ? (
          <ActivityIndicator style={styles.spinner} />
        ) : (
          <View style={styles.buttonRow}>
            <TouchableOpacity style={[styles.button, styles.cancel]} onPress={() => respond(false)}>
              <Text style={styles.buttonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.button, styles.approve]} onPress={() => respond(true)}>
              <Text style={styles.buttonText}>Approve</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: 'rgba(15,14,23,0.85)', justifyContent: 'center', padding: 24},
  card: {backgroundColor: '#1F1D33', borderRadius: 20, padding: 24, gap: 16},
  heading: {color: '#A7A9BE', fontSize: 14, textTransform: 'uppercase', letterSpacing: 1},
  summary: {color: '#FFFFFE', fontSize: 20, fontWeight: '600'},
  error: {color: '#FF6B6B'},
  outcome: {color: '#6C5CE7', fontSize: 18, fontWeight: '700', textAlign: 'center'},
  spinner: {marginTop: 8},
  buttonRow: {flexDirection: 'row', gap: 12, marginTop: 8},
  button: {flex: 1, paddingVertical: 14, borderRadius: 14, alignItems: 'center'},
  cancel: {backgroundColor: '#3A3856'},
  approve: {backgroundColor: '#6C5CE7'},
  buttonText: {color: '#FFFFFE', fontWeight: '600', fontSize: 16},
});
